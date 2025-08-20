import asyncio
from typing import List, Optional

from .models import NodeSpec, ClusterSpec
from .ssh import stream_command, get_ssh_client
from pymongo import MongoClient
from pymongo.errors import PyMongoError


async def _ssh_run(node: NodeSpec, cmd: str) -> List[str]:
    out = []
    async for line in stream_command(node, cmd):
        out.append(line)
    return out

async def install_mongodb(node: NodeSpec):
    # Rocky Linux 9 install MongoDB 7.x via official repo
    cmds = [
        "sudo tee /etc/yum.repos.d/mongodb-org-7.0.repo >/dev/null <<'EOF'\n[mongodb-org-7.0]\nname=MongoDB Repository\nbaseurl=https://repo.mongodb.org/yum/redhat/9/mongodb-org/7.0/x86_64/\ngpgcheck=1\nenabled=1\ngpgkey=https://www.mongodb.org/static/pgp/server-7.0.asc\nEOF",
        "sudo dnf -y install chrony && sudo systemctl enable --now chronyd",
        "sudo systemctl enable --now firewalld || true",
        "sudo dnf -y install mongodb-org",
        f"sudo mkdir -p {node.data_path} && sudo chown -R mongod:mongod {node.data_path}",
        f"sudo sed -i 's|^\\s*dbPath:.*|  dbPath: {node.data_path}|' /etc/mongod.conf",
        f"sudo sed -i 's|^\\s*port:.*|  port: {node.mongo_port}|' /etc/mongod.conf",
        f"sudo sed -i 's|^#*\\s*bindIp:.*|  bindIp: 0.0.0.0|' /etc/mongod.conf",
        "sudo systemctl enable --now mongod",
        f"sudo firewall-cmd --permanent --add-port={node.mongo_port}/tcp || true",
        "sudo firewall-cmd --reload || true",
    ]
    for c in cmds:
        await _ssh_run(node, c)
    return {"node": node.host, "installed": True}

async def init_replicaset(spec: ClusterSpec):
    primary = spec.nodes["primary"]
    members = []
    idx = 0
    for r, n in spec.nodes.items():
        if r == "primary":
            prio = 1
            votes = 1
            hidden = False
        elif r == "secondary":
            prio = 0
            votes = 1
            hidden = False
        else:  # analytics
            prio = 0
            votes = 0  # does not participate in elections
            hidden = False  # visible to route reads using tags
        tags = {"role": r}
        members.append({
            "_id": idx,
            "host": f"{n.host}:{n.mongo_port}",
            "priority": prio,
            "votes": votes,
            "hidden": hidden,
            "tags": tags,
        })
        idx += 1
    js = {
        "_id": spec.replset,
        "members": members,
        "protocolVersion": 1
    }
    # set replSetName on each node (append section if not present)
    for _, n in spec.nodes.items():
        await _ssh_run(n, (
            f"sudo awk 'BEGIN{{p=0}} /replication:/{{p=1}} END{{if(p==0) print \"replication:\n  replSetName: {spec.replset}\"}}' /etc/mongod.conf | sudo tee -a /etc/mongod.conf >/dev/null; "
            f"sudo sed -i 's|^\\s*replSetName:.*|  replSetName: {spec.replset}|' /etc/mongod.conf; "
            "sudo systemctl restart mongod"
        ))
    # rs.initiate
    uri = f"mongodb://{primary.host}:{primary.mongo_port}"
    client = MongoClient(uri)
    try:
        client.admin.command({"replSetInitiate": js})
    except Exception:
        pass
    # wait for PRIMARY
    for _ in range(60):
        try:
            ismaster = client.admin.command("isMaster")
            if ismaster.get("ismaster"):
                break
        except Exception:
            pass
        await asyncio.sleep(2)

async def create_users(spec: ClusterSpec):
    primary = spec.nodes["primary"]
    uri = f"mongodb://{primary.host}:{primary.mongo_port}"
    client = MongoClient(uri)
    try:
        client.admin.command("createUser", spec.creds.root_user, pwd=spec.creds.root_pass, roles=[{"role": "root", "db": "admin"}])
    except PyMongoError:
        pass
    auth_uri = f"mongodb://{spec.creds.root_user}:{spec.creds.root_pass}@{primary.host}:{primary.mongo_port}/admin"
    client = MongoClient(auth_uri)
    try:
        client[spec.db_name].command("createUser", spec.creds.app_user, pwd=spec.creds.app_pass, roles=[{"role": "readWrite", "db": spec.db_name}])
    except PyMongoError:
        pass

async def configure_security(spec: ClusterSpec):
    # Generate keyFile on primary and distribute
    import secrets
    key = secrets.token_urlsafe(96)
    primary = spec.nodes["primary"]
    key_path = "/etc/mongod.key"
    cmds = [
        f"echo '{key}' | sudo tee {key_path} >/dev/null",
        f"sudo chown mongod:mongod {key_path} && sudo chmod 400 {key_path}",
        f"sudo sed -i 's|^#*\\s*security:.*|security:\\n  authorization: enabled\\n  keyFile: {key_path}|' /etc/mongod.conf"
    ]
    for c in cmds:
        await _ssh_run(primary, c)
    # copy key to others via base64 over SSH
    for role, node in spec.nodes.items():
        if role == "primary":
            continue
        await _ssh_run(node, f"echo '{key}' | sudo tee {key_path} >/dev/null && sudo chown mongod:mongod {key_path} && sudo chmod 400 {key_path}")
        await _ssh_run(node, f"sudo sed -i 's|^#*\\s*security:.*|security:\\n  authorization: enabled\\n  keyFile: {key_path}|' /etc/mongod.conf")
    # restart all
    for _, node in spec.nodes.items():
        await _ssh_run(node, "sudo systemctl restart mongod")

async def seed_dummy_data(spec: ClusterSpec, num_docs: int, large_files):
    primary = spec.nodes["primary"]
    uri = f"mongodb://{spec.creds.root_user}:{spec.creds.root_pass}@{primary.host}:{primary.mongo_port}/admin"
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        db = client[spec.db_name]
        coll = db[spec.coll_name]
        batch = []
        import random, time
        for i in range(num_docs):
            batch.append({
                "_id": f"doc_{i}",
                "ts": time.time(),
                "cat": random.choice(["a","b","c","d"]),
                "val": random.randint(1, 10_000),
                "payload": "x" * random.randint(100, 2000)
            })
            if len(batch) >= 1000:
                coll.insert_many(batch, ordered=False)
                batch = []
        if batch:
            coll.insert_many(batch, ordered=False)
        # files to GridFS
        try:
            from gridfs import GridFS
            fs = GridFS(db)
            if large_files:
                for f in large_files:
                    fs.put(await f.read(), filename=f.filename, contentType=f.content_type)
        except Exception:
            pass
        return num_docs
    except Exception as e:
        return {"error": str(e)}

async def benchmark_cluster(spec: ClusterSpec):
    import time
    from statistics import mean
    primary = spec.nodes["primary"]
    auth_uri = f"mongodb://{spec.creds.root_user}:{spec.creds.root_pass}@{primary.host}:{primary.mongo_port}/admin"
    try:
        client = MongoClient(auth_uri, serverSelectionTimeoutMS=5000)
        db = client[spec.db_name]
        coll = db[spec.coll_name]
        # simple IOPS: N small inserts and finds
        insert_lat = []
        find_lat = []
        for i in range(100):  # Reduced for faster testing
            t0 = time.perf_counter()
            coll.insert_one({"k": i, "v": "z"})
            insert_lat.append((time.perf_counter()-t0))
        for i in range(100):
            t0 = time.perf_counter()
            list(coll.find({"k": i}).limit(1))
            find_lat.append((time.perf_counter()-t0))
        return {
            "insert_iops": round(1.0/mean(insert_lat), 2),
            "find_iops": round(1.0/mean(find_lat), 2),
            "insert_p50_ms": round(mean(insert_lat)*1000,2),
            "find_p50_ms": round(mean(find_lat)*1000,2)
        }
    except Exception as e:
        return {"error": f"Benchmark failed: {str(e)}"}

async def check_lag(spec: ClusterSpec):
    primary = spec.nodes["primary"]
    p_uri = f"mongodb://{spec.creds.root_user}:{spec.creds.root_pass}@{primary.host}:{primary.mongo_port}/admin"
    try:
        pc = MongoClient(p_uri, serverSelectionTimeoutMS=5000)
        status = pc.admin.command("replSetGetStatus")
        members = status.get("members", [])
        lag = {}
        primary_optime = None
        for m in members:
            if m.get("stateStr") == "PRIMARY":
                primary_optime = m.get("optimeDate")
        for m in members:
            name = m.get("name")
            if m.get("stateStr") == "PRIMARY":
                lag[name] = 0
            else:
                sec = 0
                if primary_optime and m.get("optimeDate"):
                    sec = (primary_optime - m.get("optimeDate")).total_seconds()
                lag[name] = sec
        return {"lag_seconds": lag, "ok": all(v == 0 for v in lag.values())}
    except Exception as e:
        return {"error": f"Health check failed: {str(e)}"}
