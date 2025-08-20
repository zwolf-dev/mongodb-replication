from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, UploadFile, Form, File, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
import orjson
from pathlib import Path

from .services.ssh import get_ssh_client, stream_command
from .services.mongo import install_mongodb, init_replicaset, create_users, configure_security, seed_dummy_data, benchmark_cluster, check_lag
from .services.models import NodeSpec, ClusterSpec

app = FastAPI(title="MongoDB Replication Orchestrator")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Persistent spec storage
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
SPEC_PATH = DATA_DIR / "cluster-spec.json"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# removed early duplicate /api/install (see final definition at bottom)

@app.post("/api/seed")
async def api_seed(
    spec_json: str = Form(...),
    num_docs: int = Form(...),
    large_files: list[UploadFile] | None = File(default=None)
):
    spec = ClusterSpec(**orjson.loads(spec_json))
    inserted = await seed_dummy_data(spec, int(num_docs), large_files)
    return {"status": "ok", "inserted": inserted}

@app.post("/api/benchmark")
async def api_benchmark(spec: ClusterSpec):
    bench = await benchmark_cluster(spec)
    return bench

@app.post("/api/health")
async def api_health(spec: ClusterSpec):
    status = await check_lag(spec)
    return status

@app.get("/api/spec")
async def api_get_spec():
    if SPEC_PATH.exists():
        try:
            data = SPEC_PATH.read_bytes()
            # Validate before returning
            spec = ClusterSpec(**orjson.loads(data))
            return spec
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to read spec: {e}")
    # Default template if not saved yet
    default = {
        "replset": "rs0",
        "creds": {
            "root_user": "rootadmin",
            "root_pass": "ChangeMeStrong!",
            "app_user": "appuser",
            "app_pass": "ChangeMeStrong!"
        },
        "db_name": "appdb",
        "coll_name": "events",
        "nodes": {
            "primary": {"host": "PRIMARY_IP", "username": "rocky", "password": "SSH_PASSWORD", "mongo_port": 27017, "role": "primary"},
            "secondary": {"host": "SECONDARY_IP", "username": "rocky", "password": "SSH_PASSWORD", "mongo_port": 27017, "role": "secondary"},
            "analytics": {"host": "ANALYTICS_IP", "username": "rocky", "password": "SSH_PASSWORD", "mongo_port": 27017, "role": "analytics"}
        }
    }
    return default

@app.post("/api/spec")
async def api_save_spec(spec: ClusterSpec):
    try:
        SPEC_PATH.write_bytes(orjson.dumps(spec.dict(), option=orjson.OPT_INDENT_2))
        return {"status": "ok", "path": str(SPEC_PATH)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save spec: {e}")

@app.websocket("/ws/ssh/{role}")
async def ws_ssh(websocket: WebSocket, role: str):
    await websocket.accept()
    try:
        # Expect NodeSpec JSON first message
        init = await websocket.receive_text()
        node = NodeSpec(**orjson.loads(init))
        async for line in stream_command(node, command=None, interactive=True, websocket=websocket):
            pass
    except WebSocketDisconnect:
        return

@app.websocket("/ws/logs/{role}")
async def ws_logs(websocket: WebSocket, role: str):
    await websocket.accept()
    try:
        init = await websocket.receive_text()
        node = NodeSpec(**orjson.loads(init))
        cmd = f"sudo tail -F {node.log_path}"
        async for line in stream_command(node, command=cmd, interactive=False):
            await websocket.send_text(line)
    except WebSocketDisconnect:
        return

@app.post("/api/test-connections")
async def api_test_connections(spec: ClusterSpec):
    results = {}
    for role, node in spec.nodes.items():
        try:
            client = await asyncio.get_event_loop().run_in_executor(None, get_ssh_client, node)
            client.close()
            results[role] = {"status": "ok", "ssh": True}
        except Exception as e:
            results[role] = {"status": "error", "ssh": False, "error": str(e)}
    return results

@app.post("/api/install")
async def api_install(spec: ClusterSpec):
    # Install MongoDB on each node and init replicaset
    results = {}
    for role, node in spec.nodes.items():
        results[role] = await install_mongodb(node)
    # Initialize replica set using primary
    await init_replicaset(spec)
    # Create suggested users
    await create_users(spec)
    # Configure keyFile + enable authorization and restart
    await configure_security(spec)
    return {"status": "ok", "results": results}

