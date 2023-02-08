#!/usr/bin/env python3

"""
A FastApi server with Google OAuth2 that
can manage code-server instances
"""

import json
import os
from string import ascii_letters, digits
from random import choice
from subprocess import Popen, DEVNULL
from typing import List

from aiohttp import ClientSession
from dotenv import load_dotenv

import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse

from modules.server_starter import start_code_server
from modules.oauth2 import generate_oauth2_url, github_oauth2

class CApp(FastAPI):
    """
    Custom FastAPI object
    """

    http_sess: ClientSession

app = CApp()
load_dotenv()

OUT_PIPE = None if os.getenv("DEBUG") == "true" else DEVNULL

# read HTML template
with open("response.html", "r", encoding = "utf8") as template_html:
    TEMPLATE_HTML = template_html.read()

# read users' local usernames
with open("users.json", "r", encoding = "utf8") as config:
    allowed_users: dict = json.load(config)

Popen(
    [
        "sudo", "mkdir", "/run/code_server_pm"
    ],
    stdout = OUT_PIPE,
    stderr = OUT_PIPE
)


Popen(
    [
        "sudo", "chown", "toby:www-data", "-R", "/run/code_server_pm"
    ],
    stdout = OUT_PIPE,
    stderr = OUT_PIPE
)

Popen(
    [
        "sudo", "mkdir", "/run/code_server_sockets"
    ],
    stdout = OUT_PIPE,
    stderr = OUT_PIPE
)

Popen(
    [
        "sudo", "chown", "toby:www-data", "-R", "/run/code_server_sockets"
    ],
    stdout = OUT_PIPE,
    stderr = OUT_PIPE
)

socket_paths = {}

LETTERS_AND_DIGITS = ascii_letters + digits

VSCODE_DOMAIN = os.getenv("VSCODE_DOMAIN")
ROOT_DOMAIN = f".{VSCODE_DOMAIN.split('.')[-2]}.{VSCODE_DOMAIN.split('.')[-1]}"
API_PASSWD = os.getenv("API_PASSWD")
EXPIRE_TIME = int(os.getenv("EXPIRE_TIME"))

@app.on_event("startup")
async def startup_event():
    """
    Startup tasks
    """

    # create session to reuse
    app.http_sess = ClientSession()

@app.get("/")
async def main_login():
    """
    Login

    Redirect user to login with Google for OAuth2
    """

    return RedirectResponse(
        url = generate_oauth2_url(),
        status_code = 302
    )

@app.get("/reset_session")
async def main_login():
    """
    Login

    Redirect user to login with Google for OAuth2
    """

    return RedirectResponse(
        url = generate_oauth2_url(redirect_uri_extension="reset_session"),
        status_code = 302
    )

@app.get("/oauth2/callback")
async def callback(code: str):
    """
    Login callback

    Get code and exchange token
    Use token to get user data
    Check for user email and local username
    Start a code-server instance for user
    Return URL to use code-server
    """

    user = await github_oauth2(app, code, allowed_users)

    # create a path prefix
    session_id = ""
    for _ in range(64):
        session_id += choice(LETTERS_AND_DIGITS)

    # start code_server
    socket_path = await start_code_server(
        user = user,
        out_pipe = OUT_PIPE,
        expire_time = EXPIRE_TIME
    )
    socket_paths[session_id] = socket_path

    with open("/run/code_server_pm/routes.json", "w", encoding = "utf8") as routes:
        routes.write(json.dumps(socket_paths))

    # redirect user to code-server
    return HTMLResponse(
        TEMPLATE_HTML.replace("%pls-replace-me%", session_id).replace("%root_domain%", ROOT_DOMAIN).replace("%vscode_domain%", VSCODE_DOMAIN)
    )

@app.get("/oauth2/callback/reset_session")
async def reset_session(code: str):
    """
    Auth user through oauth2 and reset session
    """

    user = await github_oauth2(app, code, allowed_users)
    for session_id, socket_path in socket_paths.items():
        if socket_path == f"/run/code_server_sockets/{user}_code_server.sock":
            socket_paths.pop(session_id)

    with open("/run/code_server_pm/routes.json", "w", encoding = "utf8") as routes:
        routes.write(json.dumps(socket_paths))

if __name__ == "__main__":
    uvicorn.run("main:app", uds = "/run/code_server_pm/auth-vscode.tobycm.ga.sock")
