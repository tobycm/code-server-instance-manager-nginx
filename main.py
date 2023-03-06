#!/usr/bin/env python3

"""
A FastApi server with Google OAuth2 that
can manage code-server instances
"""

import json
import os
from random import choice
from string import ascii_letters, digits

import aiofiles
import uvicorn
from aiohttp import ClientSession
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from modules.oauth2 import generate_oauth2_url, github_oauth2
from modules.server_starter import start_code_server
from modules.startup_tasks import startup_tasks


class CApp(FastAPI):
    """
    Custom FastAPI object
    """

    http_sess: ClientSession


app = CApp()
load_dotenv()

startup_tasks()

LETTERS_AND_DIGITS = ascii_letters + digits

EXPIRE_TIME = int(os.getenv("EXPIRE_TIME", "30"))

SOCKET_FOLDER = os.getenv("SOCKET_FOLDER", "/run/code_server_sockets")
API_FOLDER = os.getenv("API_FOLDER", "/run/code_server_pm")

# read HTML template
with open("response.html", "r", encoding="utf8") as template_html:
    TEMPLATE_HTML = template_html.read()

# read users' local usernames
with open("users.json", "r", encoding="utf8") as config:
    allowed_users: dict = json.load(config)


@app.on_event("startup")
async def startup_event():
    """
    Startup tasks
    """

    # create session to reuse
    app.http_sess = ClientSession()


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown tasks
    """

    # close session
    await app.http_sess.close()


@app.get("/")
async def main_login():
    """
    Login

    Redirect user to login with Google for OAuth2
    """

    return RedirectResponse(url=generate_oauth2_url(), status_code=302)


@app.get("/reset_session")
async def reset_login():
    """
    Login

    Redirect user to login with Google for OAuth2
    """

    return RedirectResponse(
        url=generate_oauth2_url(redirect_uri_extension="reset_session"), status_code=302
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

    async with aiofiles.open(
        API_FOLDER + "/routes.json", "r", encoding="utf8"
    ) as routes:
        socket_paths = json.loads(await routes.read())

    for session_id, socket_path in socket_paths.items():
        if socket_path == f"{SOCKET_FOLDER}/{user}_code_server.sock":
            return HTMLResponse(TEMPLATE_HTML.replace("%pls-replace-me%", session_id))

    # create a path prefix
    session_id = ""
    for _ in range(64):
        session_id += choice(LETTERS_AND_DIGITS)

    # start code_server
    socket_path = await start_code_server(user=user, expire_time=EXPIRE_TIME)
    socket_paths[session_id] = socket_path

    async with aiofiles.open(
        API_FOLDER + "/routes.json", "w", encoding="utf8"
    ) as routes:
        await routes.write(json.dumps(socket_paths))

    # redirect user to code-server
    return HTMLResponse(TEMPLATE_HTML.replace("%pls-replace-me%", session_id))


@app.get("/oauth2/callback/reset_session")
async def reset_session(code: str):
    """
    Auth user through oauth2 and reset session
    """

    user = await github_oauth2(app, code, allowed_users)
    for session_id, socket_path in socket_paths.items():
        if socket_path == f"{SOCKET_FOLDER}/{user}_code_server.sock":
            socket_paths.pop(session_id)

    async with aiofiles.open(
        API_FOLDER + "/routes.json", "w", encoding="utf8"
    ) as routes:
        await routes.write(json.dumps(socket_paths))


if __name__ == "__main__":
    uvicorn.run("main:app", uds=API_FOLDER + "/auth-vsus.tobycm.ga.sock")
