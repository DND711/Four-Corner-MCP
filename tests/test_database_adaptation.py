"""
Tests for query adaptation and PostgreSQL compatibility layer.
"""

from four_corner.db.database import PostgresCursorWrapper


class DummyCursor:
    def __init__(self):
        self.executed_query = None
        self.executed_params = None

    def execute(self, query, params=None):
        self.executed_query = query
        self.executed_params = params

    def fetchone(self):
        return {"id": 42}

    def fetchall(self):
        return [{"id": 42}]


def test_cursor_placeholder_adaptation():
    dummy = DummyCursor()
    wrapper = PostgresCursorWrapper(dummy)
    wrapper.execute("SELECT * FROM users WHERE email = ? AND phone = ?", ("test@example.com", "123"))
    assert "%s" in dummy.executed_query
    assert "?" not in dummy.executed_query
    assert dummy.executed_params == ("test@example.com", "123")


def test_cursor_insert_or_replace_adaptation():
    dummy = DummyCursor()
    wrapper = PostgresCursorWrapper(dummy)
    wrapper.execute("INSERT OR REPLACE INTO user_saved_units (user_id, unit_id, notes, saved_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)", ("u1", "unit1", "notes"))
    assert "ON CONFLICT (user_id, unit_id) DO UPDATE SET" in dummy.executed_query
    assert "INSERT INTO user_saved_units" in dummy.executed_query
    assert dummy.executed_params == ("u1", "unit1", "notes")


def test_cursor_inquiries_returning_id():
    dummy = DummyCursor()
    wrapper = PostgresCursorWrapper(dummy)
    wrapper.execute("INSERT INTO user_inquiries (user_id, unit_id, project_name) VALUES (?, ?, ?)", ("u1", "unit1", "Candeur"))
    assert "RETURNING id" in dummy.executed_query
    assert wrapper.lastrowid == 42
