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

from server_starter import start_code_server

class CApp(FastAPI):
    """
    Custom FastAPI object
    """

    http_sess: ClientSession

app = CApp()
load_dotenv()

OUT_PIPE = None if os.getenv("DEBUG") == "true" else DEVNULL

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

# read HTML template
with open("response.html", "r", encoding = "utf8") as template_html:
    TEMPLATE_HTML = template_html.read()

# read users' local usernames
with open("users.json", "r", encoding = "utf8") as config:
    allowed_users: dict = json.load(config)

socket_paths = {}

LETTERS_AND_DIGITS = ascii_letters + digits
SECRET_FILE = 'client_secret.json'
SCOPES = [
    "user:email"
]

VSCODE_DOMAIN = os.getenv("VSCODE_DOMAIN")
ROOT_DOMAIN = f".{VSCODE_DOMAIN.split('.')[-2]}.{VSCODE_DOMAIN.split('.')[-1]}"
API_PASSWD = os.getenv("API_PASSWD")
EXPIRE_TIME = int(os.getenv("EXPIRE_TIME"))

REDIRECT_URI = f"https://{os.getenv('OAUTH2_DOMAIN')}/oauth2/callback"

GITHUB = "https://github.com"
GITHUB_API = "https://api.github.com"

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

def generate_oauth2():
    """
    Return an authorization url for user to authenticate
    """

    authorization_url = "".join([
        f"{GITHUB}/login/oauth/authorize?",
        f"client_id={GITHUB_CLIENT_ID}&",
        f"redirect_uri={REDIRECT_URI}&",
        f"scope={' '.join(SCOPES)}&"
    ])
    return authorization_url

async def exchange_code(code: str):
    """
    Exchange OAuth2 code for user token
    """

    async with app.http_sess.get(
        url = "".join([
            f"{GITHUB}/login/oauth/access_token?" +
            f"client_id={GITHUB_CLIENT_ID}&" +
            f"client_secret={GITHUB_CLIENT_SECRET}&" +
            f"code={code}&" +
            f"redirect_uri={REDIRECT_URI}",
        ]),
        headers = {"Accept": "application/json"}
    ) as response:
        result = await response.json()
        return result["access_token"]

async def get_user_emails(access_token: str) -> List[dict]:
    """
    Get all emails of user
    """

    async with app.http_sess.get(
        url = f"{GITHUB_API}/user/emails",
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
    ) as response:
        return await response.json()

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
        url = generate_oauth2(),
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

    # exchange code for credential
    access_token = await exchange_code(code)

    # make api call to github for email
    emails = await get_user_emails(access_token)

    exists = False

    for email in emails:
        # check email for username
        user_data = allowed_users.get(email.get("email"))

        if user_data is not None:
            exists = True
            break
    if not exists:
        return "None"

    # get user's username
    user = user_data["name"]

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
        TEMPLATE_HTML.replace(
            "%pls-replace-me%", session_id
        ).replace(
            "%root_domain%", ROOT_DOMAIN
        ).replace(
            "%vscode_domain%", VSCODE_DOMAIN
        )
    )

@app.post("/get_cookie")
async def get_cookie(session_id: str, auth: str):
    """
    Return user code-server location based on session_id
    """

    if auth != API_PASSWD:
        return "None"

    return JSONResponse({
        "session_id": session_id,
        "socket_path": socket_paths.get(session_id)
    })


if __name__ == "__main__":
    uvicorn.run("main:app", uds = "/run/code_server_pm/auth-vscode.tobycm.ga.sock")
