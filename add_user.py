#!/usr/bin/python3

import json

with open("users.json", "r", encoding="utf8") as file:
    config = json.load(file)

username = input("Username: ")
email = input("Email: ")

config[email] = {
    "name": username
}

with open("users.json", "w", encoding="utf8") as file:
    file.write(json.dumps(config))
