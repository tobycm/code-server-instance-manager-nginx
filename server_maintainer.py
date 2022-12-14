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

def maintain_code_server(user, session_id, vscode_domain, root_domain, expire_time):
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
        try:
            # get heartbeat from code-server endpoint
            response = requests.get(
                f"https://{vscode_domain}/healthz", timeout=15,
                cookies = cookies
            )
            # i think .json() on this is broken so let's do it this way
            response = json.loads(response.content.decode())

            # check if expired or not
            if response["status"] == "alive":
                shutdown_count = 0
                continue

            if shutdown_count == expire_time:
                # kill code-server if expired for 60 minutes
                Popen(
                    ["sudo", "killall", "-u", user, "/usr/lib/code-server/lib/node"],
                    stdout = DEVNULL
                )

                new_routes = {}
                # clean routes when code-server is killed
                with open("/run/code_server_pm/routes.json", "r", encoding = "utf8") as file:
                    current_routes: dict = json.load(file)
                    for session_id, route in current_routes.items():
                        if route != f"/run/code_server_sockets/{user}_code_server.sock":
                            new_routes[session_id] = route

                with open("/run/code_server_pm/routes.json", "w", encoding = "utf8") as file:
                    file.write(json.dumps(new_routes))

                code_server_alive = False

            shutdown_count += 1
        except Exception as error:
            print(error)
