# code-server Instance Manager

(lots of tech debts incoming)

## How to setup

Prerequisites:

- Passwordless sudo
- Python 3.7
- A text editor
- Smileys :)

Step 1: Create and activate venv

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Step 2: Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

Step 3: Initialize configs

```bash
cp .example.env .env
cp users.example.json users.json
```

Step 4.3: Create unix users

(just use adduser)

Step 4.6: Ask for their Google Account email (sry I didn't implement GitHub)

(just hop on Discord or smth)

Step 4.9: Add them to users.json

Replace `user_email` with their email and `unix_username` with their unix username

Step 5: Change values in `.env`

`API_PASSWD`: set whatever you want
`SERVER_ADMIN`: user that is running this Python program (needs sudo perms too)
`OAUTH2_DOMAIN`: domain that point to this program
`VSCODE_DOMAIN`: domain that point to nginx in order to route requests (can leave this blank atm)

Step 6: Acquire Google OAuth2 client secret on Google Cloud Dashboard and save it in here as `client_secret.json`

Step 7: Watch [this](youtube.com/watch?v=dQw4w9WgXcQ)

Step 8: Chill

After you have set this up, please setup nginx for user routing (pls wait im uploading the tutorial on GitHub)