"""
Database connection, initialization, and query engine for Four Corner.
Supports both Supabase PostgreSQL (via DATABASE_URL) and local SQLite.
"""

import json
import os
import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from four_corner.config import DEFAULT_DB_PATH, DB_DIR
from four_corner.db.seed_data import PROJECTS_DATA


class PostgresCursorWrapper:
    """Adapts a psycopg2 cursor so it behaves consistently with sqlite3 cursor."""

    def __init__(self, cursor):
        self._cursor = cursor
        self._lastrowid = None

    def execute(self, query: str, params: Any = None):
        q = query.strip()
        # Ignore SQLite PRAGMAs on PostgreSQL
        if q.upper().startswith("PRAGMA"):
            return self

        # Adapt placeholders from ? to %s, escaping literal % if params are provided
        if params is not None and len(params) > 0:
            adapted_q = q.replace("%", "%%").replace("?", "%s")
        else:
            adapted_q = q.replace("?", "%s")

        # Adapt SQLite INSERT OR REPLACE for PostgreSQL
        if "INSERT OR REPLACE INTO projects" in adapted_q:
            adapted_q = adapted_q.replace(
                "INSERT OR REPLACE INTO projects",
                "INSERT INTO projects"
            ) + """ ON CONFLICT (id) DO UPDATE SET 
                name = EXCLUDED.name, 
                developer = EXCLUDED.developer, 
                rera_id = EXCLUDED.rera_id, 
                micro_market = EXCLUDED.micro_market, 
                promoter_legal_entity = EXCLUDED.promoter_legal_entity, 
                sanctioning_authority = EXCLUDED.sanctioning_authority, 
                approved_towers = EXCLUDED.approved_towers, 
                registered_handover_date = EXCLUDED.registered_handover_date, 
                handover_year = EXCLUDED.handover_year, 
                status = EXCLUDED.status, 
                escrow_compliant = EXCLUDED.escrow_compliant, 
                litigations_reported = EXCLUDED.litigations_reported, 
                quarterly_compliance_up_to_date = EXCLUDED.quarterly_compliance_up_to_date, 
                total_acres = EXCLUDED.total_acres, 
                clubhouse_sqft = EXCLUDED.clubhouse_sqft, 
                open_space_pct = EXCLUDED.open_space_pct"""
        elif "INSERT OR REPLACE INTO units" in adapted_q:
            adapted_q = adapted_q.replace(
                "INSERT OR REPLACE INTO units",
                "INSERT INTO units"
            ) + """ ON CONFLICT (id) DO UPDATE SET 
                tower = EXCLUDED.tower, 
                floor = EXCLUDED.floor, 
                bhk = EXCLUDED.bhk, 
                facing = EXCLUDED.facing, 
                is_corner_unit = EXCLUDED.is_corner_unit, 
                super_built_up_sqft = EXCLUDED.super_built_up_sqft, 
                carpet_area_sqft = EXCLUDED.carpet_area_sqft, 
                balcony_sqft = EXCLUDED.balcony_sqft, 
                balcony_facing = EXCLUDED.balcony_facing, 
                has_morning_sunlight = EXCLUDED.has_morning_sunlight, 
                base_rate_per_sqft = EXCLUDED.base_rate_per_sqft, 
                floor_rise_charges = EXCLUDED.floor_rise_charges, 
                corner_premium_charges = EXCLUDED.corner_premium_charges, 
                clubhouse_charges = EXCLUDED.clubhouse_charges, 
                car_parking_slots = EXCLUDED.car_parking_slots, 
                car_parking_charges = EXCLUDED.car_parking_charges, 
                infra_charges = EXCLUDED.infra_charges, 
                total_out_the_door_inr = EXCLUDED.total_out_the_door_inr, 
                total_price_cr = EXCLUDED.total_price_cr"""
        elif "INSERT OR REPLACE INTO user_saved_units" in adapted_q:
            adapted_q = adapted_q.replace(
                "INSERT OR REPLACE INTO user_saved_units",
                "INSERT INTO user_saved_units"
            ) + " ON CONFLICT (user_id, unit_id) DO UPDATE SET notes = EXCLUDED.notes, saved_at = CURRENT_TIMESTAMP"

        # Capture lastrowid for user_inquiries or serial ID inserts
        if "INSERT INTO user_inquiries" in adapted_q and "RETURNING" not in adapted_q.upper():
            adapted_q += " RETURNING id"
            if params is not None:
                self._cursor.execute(adapted_q, params)
            else:
                self._cursor.execute(adapted_q)
            res = self._cursor.fetchone()
            if res:
                self._lastrowid = res.get("id") if isinstance(res, dict) else res[0]
            return self

        if params is not None:
            self._cursor.execute(adapted_q, params)
        else:
            self._cursor.execute(adapted_q)
        return self

    def _format_row(self, row):
        if row is None:
            return None
        from decimal import Decimal
        d = dict(row)
        for k, v in d.items():
            if hasattr(v, "isoformat"):
                d[k] = v.isoformat()
            elif isinstance(v, Decimal):
                d[k] = float(v)
        return d

    def fetchone(self):
        row = self._cursor.fetchone()
        return self._format_row(row)

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [self._format_row(r) for r in rows]

    @property
    def lastrowid(self):
        return self._lastrowid

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class PostgresConnectionWrapper:
    """Wraps a psycopg2 connection to mimic sqlite3 connection semantics."""

    def __init__(self, raw_conn):
        self._raw_conn = raw_conn

    def cursor(self):
        return PostgresCursorWrapper(self._raw_conn.cursor(cursor_factory=RealDictCursor))

    def execute(self, query: str, params: Any = None):
        cur = self.cursor()
        cur.execute(query, params)
        return cur

    def commit(self):
        self._raw_conn.commit()

    def rollback(self):
        self._raw_conn.rollback()

    def close(self):
        self._raw_conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()


def sanitize_db_url(url: Optional[str]) -> Optional[str]:
    """Sanitize and URL-encode credentials in database connection URI."""
    if not url:
        return url
    url = url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if "://" in url and "@" in url:
        scheme, rest = url.split("://", 1)
        # Split on the LAST @ to isolate host_part from user:password
        auth_part, host_part = rest.rsplit("@", 1)
        if ":" in auth_part:
            user, raw_pw = auth_part.split(":", 1)
            import urllib.parse
            unquoted = urllib.parse.unquote(raw_pw)
            encoded_pw = urllib.parse.quote(unquoted, safe="")
            return f"{scheme}://{user}:{encoded_pw}@{host_part}"
    return url


class Database:
    def __init__(self, db_path: Optional[Path] = None, database_url: Optional[str] = None):
        raw_url = database_url or os.getenv("DATABASE_URL")
        self.database_url = sanitize_db_url(raw_url)
        self.is_postgres = False

        if self.database_url:
            if PSYCOPG2_AVAILABLE:
                try:
                    test_conn = psycopg2.connect(self.database_url, connect_timeout=5)
                    test_conn.close()
                    self.is_postgres = True
                    print("Connected successfully to PostgreSQL database.")
                except Exception as e:
                    print(f"Warning: Failed to connect to DATABASE_URL: {e}. Falling back to SQLite.")
                    self.is_postgres = False
            else:
                print("Warning: DATABASE_URL provided but psycopg2 is not installed. Falling back to SQLite.")

        if not self.is_postgres:
            self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.init_database()

    def get_connection(self):
        if self.is_postgres:
            raw_conn = psycopg2.connect(self.database_url)
            return PostgresConnectionWrapper(raw_conn)
        else:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn

    def init_database(self) -> None:
        if self.is_postgres:
            with self.get_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'projects') as exists"
                )
                row = cur.fetchone()
                table_exists = row.get("exists", False) if row else False

                if not table_exists:
                    schema_file = DB_DIR / "schema_supabase.sql"
                    with open(schema_file, "r", encoding="utf-8") as f:
                        sql_script = f.read()
                    cur.execute(sql_script)
                    conn.commit()
                    self.seed_database(conn)
        else:
            schema_file = DB_DIR / "schema.sql"
            with self.get_connection() as conn:
                with open(schema_file, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())

                # Auto-migrate columns if table already existed
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(oauth_codes)")
                cols = [c[1] for c in cursor.fetchall()]
                if cols and "code_challenge" not in cols:
                    cursor.execute("ALTER TABLE oauth_codes ADD COLUMN code_challenge TEXT")
                if cols and "code_challenge_method" not in cols:
                    cursor.execute("ALTER TABLE oauth_codes ADD COLUMN code_challenge_method TEXT")
                conn.commit()
                
                # Ensure all verified inventory and latest seed data are synced
                self.seed_database(conn)

    def seed_database(self, conn) -> None:
        for prj in PROJECTS_DATA:
            conn.execute(
                """
                INSERT OR REPLACE INTO projects (
                    id, name, developer, rera_id, micro_market, promoter_legal_entity,
                    sanctioning_authority, approved_towers, registered_handover_date,
                    handover_year, status, escrow_compliant, litigations_reported,
                    quarterly_compliance_up_to_date, total_acres, clubhouse_sqft, open_space_pct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prj["id"], prj["name"], prj["developer"], prj["rera_id"],
                    prj["micro_market"], prj["promoter_legal_entity"],
                    prj["sanctioning_authority"], prj["approved_towers"],
                    prj["registered_handover_date"], prj["handover_year"],
                    prj["status"], prj["escrow_compliant"],
                    prj["litigations_reported"], prj["quarterly_compliance_up_to_date"],
                    prj["total_acres"], prj["clubhouse_sqft"], prj["open_space_pct"]
                )
            )

            # Insert units
            for u in prj.get("units", []):
                base_cost = u["super_built_up_sqft"] * u["base_rate_per_sqft"]
                floor_rise = u.get("floor_rise_charges", 0)
                corner_prem = u.get("corner_premium_charges", 0)
                clubhouse = 400000
                car_parking = 600000
                infra = 350000
                subtotal = base_cost + floor_rise + corner_prem + clubhouse + car_parking + infra
                gst = int(subtotal * 0.05)
                total_inr = subtotal + gst
                total_cr = round(total_inr / 10000000.0, 2)

                conn.execute(
                    """
                    INSERT OR REPLACE INTO units (
                        id, project_id, tower, floor, bhk, facing, is_corner_unit,
                        super_built_up_sqft, carpet_area_sqft, balcony_sqft, balcony_facing,
                        has_morning_sunlight, base_rate_per_sqft, floor_rise_charges,
                        corner_premium_charges, clubhouse_charges, car_parking_slots,
                        car_parking_charges, infra_charges, total_out_the_door_inr, total_price_cr
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        u["id"], prj["id"], u["tower"], u["floor"], u["bhk"], u["facing"],
                        u["is_corner_unit"], u["super_built_up_sqft"], u["carpet_area_sqft"],
                        u["balcony_sqft"], u["balcony_facing"], u["has_morning_sunlight"],
                        u["base_rate_per_sqft"], floor_rise, corner_prem, clubhouse,
                        2, car_parking, infra, total_inr, total_cr
                    )
                )

                # Insert rooms
                conn.execute("DELETE FROM unit_rooms WHERE unit_id = ?", (u["id"],))
                for room in u.get("rooms", []):
                    conn.execute(
                        """
                        INSERT INTO unit_rooms (unit_id, room_name, dimensions_feet, carpet_sqft, facing)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (u["id"], room[0], room[1], room[2], room[3])
                    )

                # Insert balconies
                conn.execute("DELETE FROM unit_balconies WHERE unit_id = ?", (u["id"],))
                for balc in u.get("balconies", []):
                    conn.execute(
                        """
                        INSERT INTO unit_balconies (unit_id, balcony_name, dimensions_feet, orientation, morning_sunlight)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (u["id"], balc[0], balc[1], balc[2], balc[3])
                    )

            # Insert commutes
            conn.execute("DELETE FROM commute_corridors WHERE project_id = ?", (prj["id"],))
            for c in prj.get("commutes", []):
                conn.execute(
                    """
                    INSERT INTO commute_corridors (
                        project_id, destination_hub, distance_km, non_peak_mins,
                        rush_hour_morning_mins, rush_hour_evening_mins, primary_corridor,
                        key_intersections, congestion_warning
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        prj["id"], c[0], c[1], c[2], c[3], c[4], c[5],
                        json.dumps(c[6]), c[7]
                    )
                )

    def search_properties(
        self,
        micro_market: Optional[str] = None,
        max_budget_cr: Optional[float] = None,
        min_budget_cr: Optional[float] = None,
        bhk: Optional[float] = None,
        facing: Optional[str] = None,
        corner_only: bool = False,
        morning_sunlight_only: bool = False,
        ready_by_year: Optional[int] = None,
        min_carpet_sqft: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT 
                u.id as unit_id,
                p.id as project_id,
                p.name as project_name,
                p.developer,
                p.micro_market,
                p.rera_id,
                p.registered_handover_date as handover_date,
                p.handover_year,
                u.tower,
                u.floor,
                u.bhk,
                u.facing,
                u.is_corner_unit,
                u.super_built_up_sqft,
                u.carpet_area_sqft,
                ROUND(CAST((CAST(u.carpet_area_sqft AS REAL) / u.super_built_up_sqft) * 100.0 AS NUMERIC), 1) as usable_efficiency_pct,
                u.balcony_facing,
                u.has_morning_sunlight,
                u.total_price_cr,
                u.total_out_the_door_inr
            FROM units u
            JOIN projects p ON u.project_id = p.id
            WHERE 1=1
        """
        params = []

        if micro_market:
            clean_market = micro_market.strip()
            query += " AND (LOWER(p.micro_market) LIKE LOWER(?) OR LOWER(?) LIKE '%' || LOWER(p.micro_market) || '%')"
            params.extend([f"%{clean_market}%", clean_market])
        if max_budget_cr is not None:
            query += " AND u.total_price_cr <= ?"
            params.append(max_budget_cr)
        if min_budget_cr is not None:
            query += " AND u.total_price_cr >= ?"
            params.append(min_budget_cr)
        if bhk is not None:
            query += " AND (u.bhk = ? OR (u.bhk >= ? AND u.bhk < ? + 1.0))"
            params.extend([bhk, bhk, bhk])
        if facing:
            query += " AND LOWER(u.facing) LIKE LOWER(?)"
            params.append(f"%{facing.strip()}%")

        if corner_only:
            query += " AND u.is_corner_unit = 1"
        if morning_sunlight_only:
            query += " AND u.has_morning_sunlight = 1"
        if ready_by_year is not None:
            query += " AND p.handover_year <= ?"
            params.append(ready_by_year)
        if min_carpet_sqft is not None:
            query += " AND u.carpet_area_sqft >= ?"
            params.append(min_carpet_sqft)

        query += " ORDER BY u.total_price_cr ASC"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_unit_details(self, unit_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    u.*,
                    p.name as project_name,
                    p.developer,
                    p.micro_market,
                    p.rera_id,
                    p.registered_handover_date,
                    p.status as construction_status,
                    ROUND(CAST((CAST(u.carpet_area_sqft AS REAL) / u.super_built_up_sqft) * 100.0 AS NUMERIC), 1) as usable_efficiency_pct
                FROM units u
                JOIN projects p ON u.project_id = p.id
                WHERE LOWER(u.id) = LOWER(?)
                """,
                (unit_id.strip(),)
            )
            unit_row = cursor.fetchone()
            if not unit_row:
                return None
            
            unit_dict = dict(unit_row)

            # Fetch rooms
            cursor.execute(
                "SELECT room_name, dimensions_feet, carpet_sqft, facing FROM unit_rooms WHERE unit_id = ?",
                (unit_dict["id"],)
            )
            unit_dict["rooms"] = [dict(r) for r in cursor.fetchall()]

            # Fetch balconies
            cursor.execute(
                "SELECT balcony_name, dimensions_feet, orientation, morning_sunlight FROM unit_balconies WHERE unit_id = ?",
                (unit_dict["id"],)
            )
            unit_dict["balconies"] = [dict(b) for b in cursor.fetchall()]

            return unit_dict

    def get_rera_details(self, project_or_rera: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM projects
                WHERE LOWER(rera_id) = LOWER(?) OR LOWER(name) LIKE LOWER(?)
                """,
                (project_or_rera.strip(), f"%{project_or_rera.strip()}%")
            )
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    def get_commute_times(self, project_id_or_name: str, destination_hub: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT 
                    c.*,
                    p.name as project_name,
                    p.micro_market
                FROM commute_corridors c
                JOIN projects p ON c.project_id = p.id
                WHERE (LOWER(p.id) = LOWER(?) OR LOWER(p.name) LIKE LOWER(?))
            """
            params = [project_id_or_name.strip(), f"%{project_id_or_name.strip()}%"]

            if destination_hub:
                dest_clean = destination_hub.strip().lower()
                if "adp" in dest_clean:
                    query += " AND (LOWER(c.destination_hub) LIKE '%adp%' OR LOWER(c.destination_hub) LIKE '%financial district%')"
                else:
                    query += " AND LOWER(c.destination_hub) LIKE ?"
                    params.append(f"%{dest_clean}%")

            cursor.execute(query, params)
            rows = cursor.fetchall()
            res = []
            for r in rows:
                item = dict(r)
                if isinstance(item.get("key_intersections"), str):
                    try:
                        item["key_intersections"] = json.loads(item["key_intersections"])
                    except Exception:
                        pass
                res.append(item)
            return res

    def get_user_portfolio(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve all units saved by the user with full project and pricing details."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    s.saved_at,
                    s.notes,
                    u.*,
                    p.name as project_name,
                    p.developer,
                    p.micro_market,
                    p.handover_year
                FROM user_saved_units s
                JOIN units u ON s.unit_id = u.id
                JOIN projects p ON u.project_id = p.id
                WHERE s.user_id = ?
                ORDER BY s.saved_at DESC
                """,
                (user_id,)
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_user_inquiries(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve direct developer inquiries submitted by the user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM user_inquiries
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
            return [dict(r) for r in cursor.fetchall()]
