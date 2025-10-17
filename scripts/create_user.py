#!/usr/bin/env python3
import argparse
import json
import os
import sys
from getpass import getpass
try:
    from werkzeug.security import generate_password_hash
except Exception as e:
    print("Werkzeug is required. Install with: pip install Werkzeug", file=sys.stderr)
    raise


def main():
    parser = argparse.ArgumentParser(description="Create or update a users.json entry with a hashed password.")
    parser.add_argument("--file", default="users.json", help="Path to users.json (default: users.json)")
    parser.add_argument("--username", required=True, help="Username to create/update")
    parser.add_argument("--password", help="Plaintext password (omit to be prompted securely)")
    args = parser.parse_args()

    password = args.password or getpass(prompt="Password: ")
    if not password:
        print("Password is required.")
        sys.exit(1)

    users = {}
    if os.path.exists(args.file):
        with open(args.file, "r") as f:
            try:
                users = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: {args.file} exists but is not valid JSON. Overwriting.")

    users[args.username] = generate_password_hash(password)

    with open(args.file, "w") as f:
        json.dump(users, f, indent=2)

    print(f"User '{args.username}' updated in {args.file}.")


if __name__ == "__main__":
    main()

