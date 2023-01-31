from subprocess import Popen
import os

def startup_tasks(OUT_PIPE):
    # create folder for sockets
    Popen(
        [
            "sudo", "mkdir","/run/code_server_sockets"
        ],
        stdout=OUT_PIPE,
        stderr=OUT_PIPE
    )
    # and chmod it
    Popen(
        [
            "sudo", "chmod", "-R", "777", "/run/code_server_sockets"
        ],
        stdout=OUT_PIPE,
        stderr=OUT_PIPE
    )

    Popen(
        [
            "sudo", "mkdir", "/run/code_server_pm"
        ],
        stdout=OUT_PIPE,
        stderr=OUT_PIPE
    )

    Popen(
        [
            "sudo", "chown", f"{os.getenv('SERVER_ADMIN')}:www-data", "-R", "/run/code_server_pm"
        ],
        stdout=OUT_PIPE,
        stderr=OUT_PIPE
    )

    Popen(
        [
            "sudo", "chmod", "-R", "770", "/run/code_server_pm"
        ],
        stdout=OUT_PIPE,
        stderr=OUT_PIPE
    )

    with open("/run/code_server_pm/routes.json", "w", encoding = "utf8") as routes_f:
        routes_f.write("{}")
