import os
from typing import List

SCOPES = [
    "user:email"
]

REDIRECT_URI = f"https://{os.getenv('OAUTH2_DOMAIN')}/oauth2/callback"

GITHUB = "https://github.com"
GITHUB_API = "https://api.github.com"

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

def generate_oauth2_url(redirect_uri_extension: str ="") -> str:
    """
    Return an authorization url for user to authenticate
    """

    authorization_url = "".join([
        f"{GITHUB}/login/oauth/authorize?",
        f"client_id={GITHUB_CLIENT_ID}&",
        f"redirect_uri={REDIRECT_URI}/{redirect_uri_extension}&",
        f"scope={' '.join(SCOPES)}&"
    ])
    return authorization_url

async def exchange_code(app, code: str) -> str:
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

async def get_user_emails(app, access_token: str) -> List[dict]:
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

async def github_oauth2(app, code: str, allowed_users: dict) -> str:
    """
    Auth user via github
    """
    
    # exchange code for credential
    access_token = await exchange_code(app, code)

    # make api call to github for email
    emails = await get_user_emails(app, access_token)

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
    return user_data["name"]
    