"""
code-server instance maintainer

Do stuff like check if still living
else kill
"""

import json
import logging
import time
import urllib.parse
from subprocess import DEVNULL, Popen

import requests
import requests_unixsocket

requests_unixsocket.monkeypatch()


def get_heartbeat(socket_path: str):
    """
    Get heartbeat from code_server
    """

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
        ["sudo", "killall", "-u", user, "/usr/lib/code-server/lib/node"], stdout=DEVNULL
    )


def clean_old_routes(socket_path: str, routes_file: str):
    """
    Clean old routes from routes.json file
    """

    new_routes = {}
    # clean routes when code-server is killed
    with open(routes_file, "r", encoding="utf8") as file_read:
        current_routes: dict = json.load(file_read)
        for session_id, route in current_routes.items():
            if route != socket_path:
                new_routes[session_id] = route

    with open("/run/code_server_pm/routes.json", "w", encoding="utf8") as file_write:
        file_write.write(json.dumps(new_routes))


def maintain_code_server(
    user: str, expire_time: int, socket_path: str, routes_file: str
):
    """
    Main function of the file

    and blocking
    """

    shutdown_count = 0

    while True:
        time.sleep(60)

        try:
            # get heartbeat from code-server endpoint
            heartbeat = get_heartbeat(socket_path)
            if heartbeat:
                shutdown_count = 0
                continue
        except requests.exceptions.ConnectionError:
            logging.debug("code-server is not running")
            shutdown_code_server(user)
            clean_old_routes(socket_path, routes_file)
            return

        if shutdown_count == expire_time:
            # kill code-server if expired for 60 minutes
            logging.debug("code-server is expired")
            shutdown_code_server(user)
            clean_old_routes(socket_path, routes_file)
            return

        shutdown_count += 1
