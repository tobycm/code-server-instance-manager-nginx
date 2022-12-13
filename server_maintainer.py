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
            heartbeat = requests.get(
                f"https://{vscode_domain}/healthz", timeout=15,
                cookies = cookies
            ).json()

            # check if expired or not
            if heartbeat["status"] == "alive":
                shutdown_count = 0
                continue

            if shutdown_count == expire_time:
                # kill code-server if expired for 60 minutes
                Popen(
                    ["sudo", "killall", "-u", user, "/usr/lib/code-server/lib/node"],
                    stdout = DEVNULL
                )

                with open("/run/code_server_pm/routes.json", "r+", encoding = "utf8") as file:
                    data: dict = json.load(file)
                    data.pop(session_id)
                    file.write(json.dumps(data))

                code_server_alive = False

            shutdown_count += 1
        except Exception as error:
            print(error)
