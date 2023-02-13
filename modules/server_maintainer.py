"""
code-server instance maintainer

Do stuff like check if still living
else kill
"""

import time
import json
from subprocess import Popen, DEVNULL

import urllib.parse
import requests
import requests_unixsocket

requests_unixsocket.monkeypatch()

def get_heartbeat(user: str):
    """
    Get heartbeat from code_server
    """

    socket_path = f"/run/code_server_sockets/{user}_code_server.sock"

    response = requests.get(
        f"http+unix://{urllib.parse.quote(socket_path, safe = '')}/healthz", timeout=15
    ).json()

    # check if expired or not
    return True if response["status"] == "alive" else False

def shutdown_code_server(user: str):
    """
    Shutdown code_server
    """

    Popen(
        ["sudo", "killall", "-u", user, "/usr/lib/code-server/lib/node"],
        stdout = DEVNULL
    )

def clean_old_routes(user: str):
    """
    Clean old routes from routes.json file
    """

    new_routes = {}
    # clean routes when code-server is killed
    with open("/run/code_server_pm/routes.json", "r", encoding = "utf8") as file_read:
        current_routes: dict = json.load(file_read)
        for session_id, route in current_routes.items():
            if route != f"/run/code_server_sockets/{user}_code_server.sock":
                new_routes[session_id] = route

    with open("/run/code_server_pm/routes.json", "w", encoding = "utf8") as file_write:
        file_write.write(json.dumps(new_routes))

def maintain_code_server(user: str, expire_time: int):
    """
    Main function of the file

    and blocking
    """

    shutdown_count = 0
    code_server_alive = True

    while code_server_alive:
        time.sleep(60)

        try:
            # get heartbeat from code-server endpoint
            heartbeat = get_heartbeat(user)
        except requests.exceptions.ConnectionError:
            continue

        if not heartbeat:
            shutdown_count += 1

        if shutdown_count == expire_time:
            # kill code-server if expired for 60 minutes
            shutdown_code_server(user)
            clean_old_routes(user)

            code_server_alive = False

        shutdown_count += 1

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    EXPIRE_TIME = int(os.getenv("EXPIRE_TIME", 30))
    USER = input("Input your user name: ")

    maintain_code_server(
        user = USER,
        expire_time = EXPIRE_TIME
    )
