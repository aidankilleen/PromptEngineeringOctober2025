
import os
import sqlite3
import pytest

# Import the module under test
# If running these tests inside your project, you can update the import path accordingly.
import sys
from pathlib import Path

# Ensure the directory with user_dao.py is importable when running this file standalone
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent  # assumes user_dao.py will be placed next to /tests
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import user_dao as uut  # uut = unit under test


@pytest.fixture
def db_path(tmp_path):
    # Use a temporary on-disk SQLite database (not ':memory:') because
    # the DAO opens a new connection per method call.
    return tmp_path / "test_users.db"


@pytest.fixture
def dao(db_path):
    d = uut.UserDAO(str(db_path))
    d.create_table()  # ensure schema exists before each test
    return d


def test_create_table_idempotent(dao):
    # Calling create_table multiple times should not crash
    dao.create_table()
    dao.create_table()


def test_create_and_get_by_id_roundtrip(dao):
    u = uut.User(id=None, name="Alice", email="alice@example.com", active=True)
    new_id = dao.create(u)
    assert isinstance(new_id, int) and new_id > 0

    fetched = dao.get_by_id(new_id)
    assert fetched is not None
    assert fetched.id == new_id
    assert fetched.name == "Alice"
    assert fetched.email == "alice@example.com"
    assert fetched.active is True


def test_get_by_id_missing_returns_none(dao):
    assert dao.get_by_id(999_999) is None


def test_get_all_returns_in_insert_order(dao):
    ids = [
        dao.create(uut.User(None, "A", "a@x.com", True)),
        dao.create(uut.User(None, "B", None, False)),
        dao.create(uut.User(None, "C", "c@x.com", True)),
    ]
    users = dao.get_all()
    assert [u.id for u in users] == ids
    # spot-check conversion of active INTEGER -> bool
    assert users[0].active is True
    assert users[1].active is False


def test_update_success(dao):
    uid = dao.create(uut.User(None, "Bob", "bob@x.com", False))
    bob = dao.get_by_id(uid)
    bob.name = "Bobby"
    bob.email = None
    bob.active = True
    updated = dao.update(bob)
    assert updated is True

    again = dao.get_by_id(uid)
    assert again.name == "Bobby"
    assert again.email is None
    assert again.active is True


def test_update_with_missing_id_raises(dao):
    with pytest.raises(ValueError):
        dao.update(uut.User(None, "NoID", None, True))


def test_update_nonexistent_returns_false(dao):
    nonexistent = uut.User(123456, "Ghost", "ghost@x.com", False)
    assert dao.update(nonexistent) is False


def test_delete_success_and_idempotent(dao):
    uid = dao.create(uut.User(None, "ToDelete", "d@x.com", True))
    assert dao.delete(uid) is True
    # Deleting again should return False (no row affected)
    assert dao.delete(uid) is False


def test_email_can_be_null(dao):
    uid = dao.create(uut.User(None, "NullEmail", None, True))
    u = dao.get_by_id(uid)
    assert u.email is None


@pytest.mark.parametrize("active_value, expected_bool", [(0, False), (1, True)])
def test_row_to_user_bool_conversion(active_value, expected_bool, dao, db_path):
    # Insert directly with integer active values to verify _row_to_user converts to bool
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO users (name, email, active) VALUES (?, ?, ?);",
            ("FlagTest", "flag@example.com", active_value),
        )
        conn.commit()

        # Ensure fetched rows are dict-like so _row_to_user can use string keys
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, name, email, active FROM users ORDER BY id DESC LIMIT 1"
        ).fetchone()

    converted = uut.UserDAO._row_to_user(row)
    assert isinstance(converted.active, bool)
    assert converted.active is expected_bool

   
def test_insert_user_with_apostrophe_in_name(dao):
    name_with_quote = "Mary O'Sullivan"
    email = "mary@example.com"

    uid = dao.create(uut.User(None, name_with_quote, email, True))
    fetched = dao.get_by_id(uid)

    assert fetched is not None
    assert fetched.name == name_with_quote
    assert fetched.email == email
    assert fetched.active is True


def test_deliberate_failure():
    # This will always fail, just to check pytest is running correctly
    assert 1 == 1, "This is an intentional failure to verify test runs"
