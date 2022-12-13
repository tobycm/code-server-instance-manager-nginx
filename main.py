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

from google_auth_oauthlib.flow import Flow

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
    stdout=OUT_PIPE
)
# and chmod it
Popen(
    [
        "sudo", "chmod", "-R", "777", "/run/code_server_sockets"
    ],
    stdout=OUT_PIPE
)

Popen(
    [
        "sudo", "mkdir", "/run/code_server_pm"
    ],
    stdout=OUT_PIPE
)

Popen(
    [
        "sudo", "chown", f"{os.getenv('SERVER_ADMIN')}:www-data", "-R", "/run/code_server_pm"
    ],
    stdout=OUT_PIPE
)

Popen(
    [
        "sudo", "chmod", "770", "/run/code_server_pm"
    ],
    stdout=OUT_PIPE
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
api_scopes = [
    'https://www.googleapis.com/auth/userinfo.email',
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]

VSCODE_DOMAIN = os.getenv("VSCODE_DOMAIN")
ROOT_DOMAIN = f".{VSCODE_DOMAIN.split('.')[-2]}.{VSCODE_DOMAIN.split('.')[-1]}"
API_PASSWD = os.getenv("API_PASSWD")
EXPIRE_TIME = int(os.getenv("EXPIRE_TIME"))

REDIRECT_URI = f"https://{os.getenv('OAUTH2_DOMAIN')}/oauth2/callback"

def oauth2(client_secret_file: str, scopes: List[str], redirect_uri: str):
    """
    Return an authorization url for user to authenticate
    """

    # Use the client_secret.json file to identify the application requesting
    # authorization. The client ID (from that file) and access scopes are required.
    flow = Flow.from_client_secrets_file(
        client_secret_file,
        scopes=scopes
    )

    # Indicate where the API server will redirect the user after the user completes
    # the authorization flow. The redirect URI is required. The value must exactly
    # match one of the authorized redirect URIs for the OAuth 2.0 client, which you
    # configured in the API Console. If this value doesn't match an authorized URI,
    # you will get a 'redirect_uri_mismatch' error.
    flow.redirect_uri = redirect_uri

    # Generate URL for request to Google's OAuth 2.0 server.
    # Use kwargs to set optional request parameters.
    authorization_url, _ = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true'
    )
    # return auth url
    return authorization_url

def exchange_code(client_secret_file: str, scopes: List[str], redirect_uri: str, code: str):
    """
    Exchange OAuth2 code for user token
    """

    # make a flow with credentials from secret file
    flow = Flow.from_client_secrets_file(
        client_secret_file,
        scopes = scopes
    )
    # set redirect uri
    flow.redirect_uri = redirect_uri

    # fetch token in exchange for code
    flow.fetch_token(code = code)
    # return user credentials
    return flow.credentials

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
        url = oauth2(
            SECRET_FILE,
            api_scopes,
            REDIRECT_URI
        ),
        status_code=302
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
    credential = exchange_code(SECRET_FILE, api_scopes, REDIRECT_URI, code)
    access_token = str(credential.token)

    # make api call to google for email
    async with app.http_sess.get(
        url = "https://www.googleapis.com/oauth2/v2/userinfo?access_token=" + access_token
    ) as response:
        data = await response.json()
        email = data["email"]

    # check email for username
    user_data = allowed_users.get(email)

    if user_data is None:
        return "None"

    # get user's username
    user = user_data["name"]
    # create a path prefix
    session_id = ""
    for _ in range(64):
        session_id += choice(LETTERS_AND_DIGITS)

    # start code_server
    socket_path = await start_code_server(user, session_id, VSCODE_DOMAIN, ROOT_DOMAIN, OUT_PIPE, EXPIRE_TIME)
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
