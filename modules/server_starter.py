"""
Handle code-server startup and Caddyfile routing
"""

import asyncio
import os
from subprocess import Popen
from threading import Thread

from dotenv import load_dotenv

load_dotenv()

from .server_maintainer import maintain_code_server

SOCKET_FOLDER = os.getenv("SOCKET_FOLDER", "/run/code_server_sockets")


async def start_code_server(user: str, expire_time: int):
    """
    Start code-server and prepare for maintain thread
    """

    socket_path = f"{SOCKET_FOLDER}/{user}_code_server.sock"

    Popen(["sudo", "rm", "-f", socket_path])

    Popen(["sudo", "runuser", "-l", user, "-c", f"code-server --socket {socket_path}"])

    while True:
        if os.path.exists(socket_path):
            break
        await asyncio.sleep(0.1)

    Popen(["sudo", "chown", ":www-data", socket_path])

    Popen(["sudo", "chmod", "770", socket_path])

    maintain_thread = Thread(
        target=maintain_code_server,
        args=(
            user,
            expire_time,
        ),
    )

    maintain_thread.start()

    return socket_path
