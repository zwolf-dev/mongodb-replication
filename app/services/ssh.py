import asyncio
import base64
from typing import AsyncGenerator, Optional
import paramiko

from .models import NodeSpec


def get_ssh_client(node: NodeSpec) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if node.pkey:
        key = paramiko.RSAKey.from_private_key_file(node.pkey)
        client.connect(node.host, port=node.port, username=node.username, pkey=key, look_for_keys=False)
    else:
        client.connect(node.host, port=node.port, username=node.username, password=node.password, look_for_keys=False)
    return client

async def stream_command(node: NodeSpec, command: Optional[str], interactive: bool = False, websocket=None) -> AsyncGenerator[str, None]:
    # Run a command or interactive shell and stream output lines
    loop = asyncio.get_event_loop()
    client = await loop.run_in_executor(None, get_ssh_client, node)
    try:
        if interactive:
            channel = client.invoke_shell()
            await websocket.send_text("Connected. Type commands. Exit with 'exit' or Ctrl-D'.")
            while True:
                msg = await websocket.receive_text()
                channel.send(msg + "\n")
                await asyncio.sleep(0.05)
                while channel.recv_ready():
                    data = channel.recv(4096).decode()
                    await websocket.send_text(data)
        else:
            stdin, stdout, stderr = client.exec_command(command)
            for line in iter(stdout.readline, ""):
                yield line
    finally:
        client.close()
