import os
from subprocess import Popen

from dotenv import load_dotenv

load_dotenv()

SERVER_ADMIN = os.getenv("SERVER_ADMIN")
if SERVER_ADMIN is None:
    exit("SERVER_ADMIN is not set")

SOCKET_FOLDER = os.getenv("SOCKET_FOLDER", "/run/code_server_sockets")
API_FOLDER = os.getenv("API_FOLDER", "/run/code_server_pm")


def startup_tasks():
    # create folder for sockets
    Popen(["sudo", "mkdir", "-p", SOCKET_FOLDER])
    # and chmod it
    Popen(["sudo", "chmod", "-R", "777", SOCKET_FOLDER])

    Popen(["sudo", "mkdir", "-p", API_FOLDER])

    Popen(["sudo", "chown", SERVER_ADMIN + ":www-data", "-R", API_FOLDER])

    Popen(["sudo", "chmod", "-R", "770", API_FOLDER])

    with open(API_FOLDER + "/routes.json", "w+", encoding="utf8") as routes_f:
        routes_f.write("{}")
