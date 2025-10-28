#!/usr/bin/env python3
"""
user_dao.py - A simple Data Access Object (DAO) for the 'users' table in SQLite.

Schema expected:
    CREATE TABLE IF NOT EXISTS users (
        id     INTEGER PRIMARY KEY AUTOINCREMENT,
        name   TEXT    NOT NULL,
        email  TEXT,
        active INTEGER NOT NULL CHECK (active IN (0, 1))
    );

Usage (examples at bottom):
    dao = UserDAO("users.db")
    dao.create_table()  # safe to call repeatedly

    user_id = dao.create(User(None, "Alice", "alice@example.com", True))
    user = dao.get_by_id(user_id)
    users = dao.get_all()

    user.name = "Alice Smith"
    dao.update(user)

    dao.delete(user_id)
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class User:
    id: Optional[int]
    name: str
    email: Optional[str]
    active: bool


class UserDAO:
    def __init__(self, db_path: str = "users.db") -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # access columns by name
        return conn

    # --- Schema management -------------------------------------------------

    def create_table(self) -> None:
        sql = """
        CREATE TABLE IF NOT EXISTS users (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            name   TEXT    NOT NULL,
            email  TEXT,
            active INTEGER NOT NULL CHECK (active IN (0, 1))
        );
        """
        with self._connect() as conn:
            conn.execute(sql)
            conn.commit()

    # --- CRUD --------------------------------------------------------------

    def create(self, user: User) -> int:
        """Insert a new user. Returns new user id."""
        sql = "INSERT INTO users (name, email, active) VALUES (?, ?, ?);"
        params = (user.name, user.email, int(user.active))
        with self._connect() as conn:
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.lastrowid

    def get_by_id(self, user_id: int) -> Optional[User]:
        sql = "SELECT id, name, email, active FROM users WHERE id = ?;"
        with self._connect() as conn:
            row = conn.execute(sql, (user_id,)).fetchone()
        if not row:
            return None
        return self._row_to_user(row)

    def get_all(self) -> List[User]:
        sql = "SELECT id, name, email, active FROM users ORDER BY id;"
        with self._connect() as conn:
            rows = conn.execute(sql).fetchall()
        return [self._row_to_user(r) for r in rows]

    def update(self, user: User) -> bool:
        """Update an existing user. Returns True if a row was updated."""
        if user.id is None:
            raise ValueError("User.id must be set to update")
        sql = """
        UPDATE users
        SET name = ?, email = ?, active = ?
        WHERE id = ?;
        """
        params = (user.name, user.email, int(user.active), user.id)
        with self._connect() as conn:
            cur = conn.execute(sql, params)
            conn.commit()
            return cur.rowcount > 0

    def delete(self, user_id: int) -> bool:
        """Delete a user by id. Returns True if a row was deleted."""
        sql = "DELETE FROM users WHERE id = ?;"
        with self._connect() as conn:
            cur = conn.execute(sql, (user_id,))
            conn.commit()
            return cur.rowcount > 0

    # --- Helpers -----------------------------------------------------------

    @staticmethod
    def _row_to_user(row: sqlite3.Row) -> User:
        return User(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            active=bool(row["active"]),
        )


# --- Demo / quick test -----------------------------------------------------
if __name__ == "__main__":
    dao = UserDAO("users.db")
    dao.create_table()  # safe if table already exists

    # Create a few users
    ids = []
    ids.append(dao.create(User(None, "Alice", "alice@example.com", True)))
    ids.append(dao.create(User(None, "Bob", "bob@example.com", False)))

    print("All users after inserts:")
    for u in dao.get_all():
        print(u)

    # Read one
    one = dao.get_by_id(ids[0])
    print("\nGet by id:", one)

    # Update
    if one:
        one.name = "Alice Smith"
        one.active = True
        dao.update(one)

    print("\nAll users after update:")
    for u in dao.get_all():
        print(u)

    # Delete Bob
    dao.delete(ids[1])

    print("\nAll users after delete:")
    for u in dao.get_all():
        print(u)
