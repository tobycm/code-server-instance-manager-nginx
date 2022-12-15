"""
code-server instance maintainer

Do stuff like check if still living
else kill
"""

import time
import json
from subprocess import Popen, DEVNULL

import requests
from requests.cookies import RequestsCookieJar

def get_heartbeat(vscode_domain: str, cookies: RequestsCookieJar):
    """
    Get heartbeat from code_server
    """
    response = requests.get(
        f"https://{vscode_domain}/healthz", timeout=15,
        cookies = cookies
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

def maintain_code_server(
    user: str,
    session_id: str,
    vscode_domain: str,
    root_domain: str,
    expire_time: int
):
    """
    Main function of the file

    and blocking
    """

    shutdown_count = 0
    cookies = RequestsCookieJar()
    cookies.set("session_id", session_id, domain=root_domain)
    code_server_alive = True

    while code_server_alive:
        time.sleep(60)
        # get heartbeat from code-server endpoint
        heartbeat = get_heartbeat(vscode_domain, cookies)

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

    VSCODE_DOMAIN = os.getenv("VSCODE_DOMAIN")
    ROOT_DOMAIN = f".{VSCODE_DOMAIN.split('.')[-2]}.{VSCODE_DOMAIN.split('.')[-1]}"
    EXPIRE_TIME = int(os.getenv("EXPIRE_TIME"))

    maintain_code_server(
        input("Input your user name: "),
        input("Input your session id: "),
        VSCODE_DOMAIN,
        ROOT_DOMAIN,
        EXPIRE_TIME
    )
