#!/usr/bin/env python3
"""
create_users_db.py - Create an SQLite database with a 'users' table
and insert 5 test records.
"""

import sqlite3
import os

DB_NAME = "users.db"

def main():
    # Remove the database if it already exists (start fresh)
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    # Connect to the database (creates it if it doesn't exist)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Create the users table
    cur.execute("""
    CREATE TABLE users (
        id     INTEGER PRIMARY KEY AUTOINCREMENT,
        name   TEXT    NOT NULL,
        email  TEXT,
        active INTEGER NOT NULL CHECK (active IN (0, 1))
    );
    """)

    # Insert 5 test records
    users = [
        ("Alice", "alice@example.com", 1),
        ("Bob", "bob@example.com", 0),
        ("Carol", "carol@example.com", 1),
        ("Dan", "dan@example.com", 0),
        ("Eve", "eve@example.com", 1),
    ]

    cur.executemany("INSERT INTO users (name, email, active) VALUES (?, ?, ?);", users)

    # Commit and close
    conn.commit()
    conn.close()

    print(f"Database '{DB_NAME}' created with 5 test users.")

if __name__ == "__main__":
    main()
