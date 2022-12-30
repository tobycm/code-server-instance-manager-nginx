# code-server Instance Manager

(lots of tech debts incoming)

## How to setup

### Prerequisites

- Passwordless sudo
- Python 3.7
- A text editor
- Smileys :)

### Step 1: Create and activate venv

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

### Step 3: Initialize configs

```bash
cp .example.env .env
cp users.example.json users.json
```

### Step 4.3: Create unix users

(just use `adduser`)

### Step 4.6: Ask for their Google Account email (sorry I didn't implement GitHub)

(just hop on Discord or something)

### Step 4.9: Add them to users.json

Replace `user_email` with their email and `unix_username` with their unix username

### Step 5: Change values in `.env`

`API_PASSWD`: set whatever you want

`SERVER_ADMIN`: user that is running this Python program (needs sudo perms too)

`OAUTH2_DOMAIN`: domain that point to this program

`VSCODE_DOMAIN`: domain that point to nginx in order to route requests (can leave this blank atm)

`EXPIRE_TIME`: minutes after code-server expired to shutdown

### Step 6: Acquire GitHub OAuth2 client ID and secret

After you have acquired these sacred objects please put them in the following order (in `.env`):

`GITHUB_CLIENT_ID`: GitHub client ID

`GITHUB_CLIENT_SECRET`: GitHub client secret

### Step outside and enjoy the sunlight view

You can set `DEBUG` to true if you want Popen's logs to output to stdout

### Step 7: Watch [this](youtube.com/watch?v=dQw4w9WgXcQ)

### Step 8: Chill

After you have set this up, please setup [nginx for user routing](https://github.com/tobycm/nginx-code-server-router/)
