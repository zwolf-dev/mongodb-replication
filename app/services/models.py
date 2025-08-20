from pydantic import BaseModel, Field
from typing import Dict, Optional

class NodeSpec(BaseModel):
    host: str
    port: int = 22
    username: str
    password: Optional[str] = None
    pkey: Optional[str] = None  # PEM string
    mongo_port: int = 27017
    data_path: str = "/var/lib/mongo"
    log_path: str = "/var/log/mongodb/mongod.log"
    role: str = Field(description="primary|secondary|analytics")

class Creds(BaseModel):
    root_user: str = "rootadmin"
    root_pass: str
    app_user: str = "appuser"
    app_pass: str

class ClusterSpec(BaseModel):
    nodes: Dict[str, NodeSpec]
    replset: str = "rs0"
    creds: Creds
    db_name: str = "appdb"
    coll_name: str = "events"
