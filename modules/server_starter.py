"""
Handle code-server startup and Caddyfile routing
"""

import asyncio
import grp
import os
import pwd
from subprocess import Popen
from threading import Thread

from dotenv import load_dotenv

load_dotenv()

from .server_maintainer import maintain_code_server

SOCKET_FOLDER = os.getenv("SOCKET_FOLDER", "/run/code_server_sockets")
API_FOLDER = os.getenv("API_FOLDER", "/run/code_server_pm")


async def start_code_server(user: str, expire_time: int):
    """
    Start code-server and prepare for maintain thread
    """

    socket_path = f"{SOCKET_FOLDER}/{user}_code_server.sock"

    Popen(["sudo", "rm", "-f", socket_path])

    Popen(["sudo", "runuser", "-l", user, "-c", f"code-server --socket {socket_path}"])

    user_id = pwd.getpwnam(user).pw_uid
    www_data_group_id = grp.getgrnam("www-data").gr_gid

    while not os.path.exists(socket_path):
        await asyncio.sleep(0.1)

    while True:
        socket_file_stat = os.stat(socket_path)
        if (socket_file_stat.st_gid == www_data_group_id) and (
            socket_file_stat.st_uid == user_id
        ):
            break

        Popen(["sudo", "chown", ":www-data", socket_path])
        Popen(["sudo", "chmod", "770", socket_path])

        await asyncio.sleep(0.25)

    maintain_thread = Thread(
        target=maintain_code_server,
        args=(
            user,
            expire_time,
            socket_path,
            API_FOLDER + "/routes.json",
        ),
    )

    maintain_thread.start()

    return socket_path
