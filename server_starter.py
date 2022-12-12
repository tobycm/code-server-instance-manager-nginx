"""
Handle code-server startup and Caddyfile routing
"""

from subprocess import Popen
from threading import Thread
import asyncio

from server_maintainer import maintain_code_server

async def start_code_server(user: str, session_id: str, vscode_domain: str, out_pipe, expire_time: int):
    """
    Start code-server and prepare for maintain thread
    """

    socket_path = f"/run/code_server_sockets/{user}_code_server.sock"

    Popen(
        [
            "sudo", "runuser", "-l", user, "-c",
            f"code-server --socket {socket_path}"
        ],
        stdout=out_pipe
    )

    await asyncio.sleep(4)

    Popen(
        [
            "sudo", "chown", ":www-data", socket_path
        ],
        stdout=out_pipe
    )

    Popen(
        [
            "sudo", "chmod", "770", socket_path
        ],
        stdout=out_pipe
    )

    maintain_thread = Thread(
        target=maintain_code_server, args=[user, session_id, vscode_domain, expire_time]
    )

    maintain_thread.start()

    return socket_path
