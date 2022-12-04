"""
code-server instance maintainer

Do stuff like check if still living
else kill
"""

import time
import json
from subprocess import Popen

import requests
from requests.cookies import RequestsCookieJar

def maintain_code_server(user, session_id, vscode_domain):
    """
    Main function of the file

    and blocking
    """

    shutdown_count = 0
    cookies = RequestsCookieJar()
    cookies.set("session_id", session_id, domain="vscode.tobycm.ga")

    while True:
        time.sleep(60)
        # get heartbeat from code-server endpoint
        heartbeat = requests.get(
            f"https://{vscode_domain}/{session_id}/healthz", timeout=15,
            cookies = cookies
        ).json()

        # check if expired or not
        if heartbeat["status"] != "alive":
            if shutdown_count == 30:
                # kill code-server if expired for 30 minutes
                Popen(
                    ["sudo", "killall", "-u", user, "/usr/lib/code-server/lib/node"]
                )

                with open("routes.json", "r+", encoding = "utf8") as file:
                    data: dict = json.load(file)
                    data.pop(session_id)
                    file.write(json.dumps(data))

                break

            shutdown_count += 1
        else:
            shutdown_count = 0
