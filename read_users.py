#!/usr/bin/env python3
"""
read_users.py - Read all users from the users.db SQLite database
and map them into User objects.
"""

import sqlite3
from dataclasses import dataclass

# Define a User object
@dataclass
class User:
    id: int
    name: str
    email: str | None
    active: bool

def get_all_users(db_path: str = "users.db") -> list[User]:
    """Fetch all users from the database and return them as a list of User objects."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id, name, email, active FROM users")
    rows = cur.fetchall()

    users = []
    for row in rows:
        user = User(
            id=row[0],
            name=row[1],
            email=row[2],
            active=bool(row[3])  # convert 0/1 into True/False
        )
        users.append(user)

    conn.close()
    return users

if __name__ == "__main__":
    users = get_all_users()
    for user in users:
        print(user)
