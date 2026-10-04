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


def test_row_dict_and_cursor_indexing():
    from four_corner.db.database import RowDict
    import json

    # Direct RowDict testing
    rd = RowDict({"count": 25, "total_value": 150.5})
    assert rd[0] == 25
    assert rd[1] == 150.5
    assert rd["count"] == 25
    assert rd.get("count") == 25
    assert rd.get(0) == 25
    assert rd.get(1) == 150.5
    assert rd.get(99, "default") == "default"
    assert dict(rd) == {"count": 25, "total_value": 150.5}
    assert json.loads(json.dumps(rd)) == {"count": 25, "total_value": 150.5}

    # PostgresCursorWrapper fetchone and fetchall
    class MultiColDummy:
        def fetchone(self):
            return {"micro_market": "Kokapet", "search_count": 88}

        def fetchall(self):
            return [
                {"micro_market": "Kokapet", "search_count": 88},
                {"micro_market": "Tellapur", "search_count": 45}
            ]

    wrapper = PostgresCursorWrapper(MultiColDummy())
    single = wrapper.fetchone()
    assert single[0] == "Kokapet"
    assert single[1] == 88
    assert single["micro_market"] == "Kokapet"

    all_rows = wrapper.fetchall()
    extracted = [{"name": r[0], "count": r[1]} for r in all_rows]
    assert extracted == [
        {"name": "Kokapet", "count": 88},
        {"name": "Tellapur", "count": 45}
    ]
