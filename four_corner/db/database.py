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


class RowDict(dict):
    """A dictionary subclass that also supports integer indexing like sqlite3.Row."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._values = list(self.values())

    def __getitem__(self, key):
        if isinstance(key, int):
            try:
                return self._values[key]
            except IndexError:
                return None
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._values = list(self.values())

    def get(self, key, default=None):
        if isinstance(key, int):
            try:
                return self._values[key]
            except IndexError:
                return default
        return super().get(key, default)


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
                open_space_pct = EXCLUDED.open_space_pct,
                verification_status = EXCLUDED.verification_status,
                tagline = EXCLUDED.tagline,
                project_type = EXCLUDED.project_type,
                official_url = EXCLUDED.official_url,
                is_rera_registered = EXCLUDED.is_rera_registered,
                total_units = EXCLUDED.total_units,
                road_width_feet = EXCLUDED.road_width_feet,
                water_source = EXCLUDED.water_source,
                assigned_badge = EXCLUDED.assigned_badge,
                auditor_id = EXCLUDED.auditor_id,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                construction_stage = EXCLUDED.construction_stage,
                road_condition = EXCLUDED.road_condition,
                red_flag_notes = EXCLUDED.red_flag_notes,
                hero_image_url = EXCLUDED.hero_image_url,
                gallery_images = EXCLUDED.gallery_images,
                walkthrough_video_url = EXCLUDED.walkthrough_video_url,
                drone_footage_url = EXCLUDED.drone_footage_url,
                brochure_pdf_url = EXCLUDED.brochure_pdf_url,
                master_plan_url = EXCLUDED.master_plan_url,
                cost_sheet_pdf_url = EXCLUDED.cost_sheet_pdf_url,
                site_progress_photos = EXCLUDED.site_progress_photos"""
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
                total_price_cr = EXCLUDED.total_price_cr,
                floor_plan_image_url = EXCLUDED.floor_plan_image_url"""
        elif "INSERT OR REPLACE INTO user_saved_units" in adapted_q:
            adapted_q = adapted_q.replace(
                "INSERT OR REPLACE INTO user_saved_units",
                "INSERT INTO user_saved_units"
            ) + " ON CONFLICT (user_id, unit_id) DO UPDATE SET notes = EXCLUDED.notes, saved_at = CURRENT_TIMESTAMP"
        elif "INSERT OR REPLACE INTO users" in adapted_q:
            adapted_q = adapted_q.replace(
                "INSERT OR REPLACE INTO users",
                "INSERT INTO users"
            ) + """ ON CONFLICT (id) DO UPDATE SET 
                email = EXCLUDED.email, 
                name = EXCLUDED.name, 
                phone = EXCLUDED.phone, 
                micro_market_pref = EXCLUDED.micro_market_pref, 
                budget_max_cr = EXCLUDED.budget_max_cr, 
                bhk_pref = EXCLUDED.bhk_pref, 
                intent_score = EXCLUDED.intent_score, 
                buyer_tier = EXCLUDED.buyer_tier, 
                intent_breakdown = EXCLUDED.intent_breakdown"""
        elif "INSERT OR REPLACE INTO search_events" in adapted_q:
            adapted_q = adapted_q.replace(
                "INSERT OR REPLACE INTO search_events",
                "INSERT INTO search_events"
            ) + " ON CONFLICT (id) DO NOTHING"

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
        return RowDict(d)

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
                    # Ensure projects table has all extended columns
                    try:
                        cur.execute("""
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS verification_status TEXT DEFAULT 'Verified';
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_status TEXT DEFAULT 'APPROVED_PUBLIC';
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS overall_risk_level TEXT DEFAULT 'LOW';
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS public_visibility INTEGER DEFAULT 1;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS next_review_at TIMESTAMP;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS promoter_id TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS district TEXT DEFAULT 'Hyderabad';
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS mandal TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS village TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS boundary_geometry TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS address TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS tagline TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS project_type TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS official_url TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_rera_registered INTEGER DEFAULT 1;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS total_units INTEGER;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS road_width_feet REAL;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS water_source TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS assigned_badge TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS auditor_id TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS latitude REAL;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS longitude REAL;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS construction_stage TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS road_condition TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS red_flag_notes TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS hero_image_url TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS gallery_images TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS walkthrough_video_url TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS drone_footage_url TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS brochure_pdf_url TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS master_plan_url TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS cost_sheet_pdf_url TEXT;
                            ALTER TABLE projects ADD COLUMN IF NOT EXISTS site_progress_photos TEXT;
                            ALTER TABLE units ADD COLUMN IF NOT EXISTS floor_plan_image_url TEXT;
                        """)
                        conn.commit()
                        cur.execute("""
                            UPDATE projects SET verification_status = 'Verified' WHERE verification_status IS NULL;
                            UPDATE projects SET project_status = 'APPROVED_PUBLIC' WHERE project_status IS NULL;
                            UPDATE projects SET overall_risk_level = 'LOW' WHERE overall_risk_level IS NULL;
                            UPDATE projects SET public_visibility = 1 WHERE public_visibility IS NULL;
                            UPDATE projects SET address = micro_market || ', Hyderabad' WHERE address IS NULL;
                        """)
                        conn.commit()
                    except Exception as e:
                        print(f"Notice during PostgreSQL projects migration: {e}")
                        conn.rollback()

                    # Ensure B-RISE intent scoring columns exist
                    try:
                        cur.execute("""
                            ALTER TABLE users ADD COLUMN IF NOT EXISTS intent_score INTEGER NOT NULL DEFAULT 0;
                            ALTER TABLE users ADD COLUMN IF NOT EXISTS buyer_tier TEXT NOT NULL DEFAULT 'CASUAL_BROWSER';
                            ALTER TABLE users ADD COLUMN IF NOT EXISTS intent_breakdown TEXT;
                            ALTER TABLE users ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                        """)
                        conn.commit()
                    except Exception as e:
                        print(f"Notice during PostgreSQL users migration: {e}")
                        conn.rollback()

                    # Ensure search_events table exists
                    try:
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS search_events (
                                id TEXT PRIMARY KEY,
                                user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
                                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                micro_market TEXT,
                                max_budget_cr REAL,
                                min_budget_cr REAL,
                                bhk REAL,
                                facing TEXT,
                                corner_only INTEGER DEFAULT 0,
                                morning_sunlight_only INTEGER DEFAULT 0,
                                ready_by_year INTEGER,
                                min_carpet_sqft INTEGER,
                                results_count INTEGER DEFAULT 0,
                                unit_ids_returned TEXT DEFAULT '',
                                project_names_returned TEXT DEFAULT ''
                            );
                            CREATE INDEX IF NOT EXISTS idx_search_events_user ON search_events(user_id);
                            CREATE INDEX IF NOT EXISTS idx_search_events_time ON search_events(timestamp);
                        """)
                        conn.commit()
                    except Exception as e:
                        print(f"Notice during PostgreSQL search_events migration: {e}")
                        conn.rollback()

                    try:
                        self.seed_database(conn)
                        self.seed_telemetry_and_buyers(conn)
                    except Exception as e:
                        print(f"Notice during PostgreSQL seeding: {e}")
                        conn.rollback()
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

                # Auto-migrate users columns for intent scoring
                cursor.execute("PRAGMA table_info(users)")
                u_cols = [c[1] for c in cursor.fetchall()]
                if u_cols and "intent_score" not in u_cols:
                    cursor.execute("ALTER TABLE users ADD COLUMN intent_score INTEGER DEFAULT 0")
                if u_cols and "buyer_tier" not in u_cols:
                    cursor.execute("ALTER TABLE users ADD COLUMN buyer_tier TEXT DEFAULT 'CASUAL_BROWSER'")
                if u_cols and "intent_breakdown" not in u_cols:
                    cursor.execute("ALTER TABLE users ADD COLUMN intent_breakdown TEXT")
                if u_cols and "last_activity_at" not in u_cols:
                    cursor.execute("ALTER TABLE users ADD COLUMN last_activity_at TIMESTAMP DEFAULT NULL")

                # Auto-migrate projects columns
                cursor.execute("PRAGMA table_info(projects)")
                p_cols = [c[1] for c in cursor.fetchall()]
                for col_name, col_type, col_def in [
                    ("verification_status", "TEXT", "'Verified'"),
                    ("tagline", "TEXT", "NULL"),
                    ("project_type", "TEXT", "NULL"),
                    ("official_url", "TEXT", "NULL"),
                    ("is_rera_registered", "INTEGER", "1"),
                    ("total_units", "INTEGER", "NULL"),
                    ("road_width_feet", "REAL", "NULL"),
                    ("water_source", "TEXT", "NULL"),
                    ("assigned_badge", "TEXT", "NULL"),
                    ("auditor_id", "TEXT", "NULL"),
                    ("latitude", "REAL", "NULL"),
                    ("longitude", "REAL", "NULL"),
                    ("construction_stage", "TEXT", "NULL"),
                    ("road_condition", "TEXT", "NULL"),
                    ("red_flag_notes", "TEXT", "NULL"),
                    ("hero_image_url", "TEXT", "NULL"),
                    ("gallery_images", "TEXT", "NULL"),
                    ("walkthrough_video_url", "TEXT", "NULL"),
                    ("drone_footage_url", "TEXT", "NULL"),
                    ("brochure_pdf_url", "TEXT", "NULL"),
                    ("master_plan_url", "TEXT", "NULL"),
                    ("cost_sheet_pdf_url", "TEXT", "NULL"),
                    ("site_progress_photos", "TEXT", "NULL"),
                    ("promoter_id", "TEXT", "NULL"),
                    ("district", "TEXT", "'Hyderabad'"),
                    ("mandal", "TEXT", "NULL"),
                    ("village", "TEXT", "NULL"),
                    ("boundary_geometry", "TEXT", "NULL"),
                    ("project_status", "TEXT", "'APPROVED_PUBLIC'"),
                    ("overall_risk_level", "TEXT", "'LOW'"),
                    ("public_visibility", "INTEGER", "1"),
                    ("next_review_at", "TIMESTAMP", "NULL"),
                    ("address", "TEXT", "NULL"),
                    ("updated_at", "TIMESTAMP", "NULL"),
                ]:
                    if p_cols and col_name not in p_cols:
                        cursor.execute(f"ALTER TABLE projects ADD COLUMN {col_name} {col_type} DEFAULT {col_def}")
                cursor.execute("UPDATE projects SET verification_status = 'Verified' WHERE verification_status IS NULL")
                cursor.execute("UPDATE projects SET project_status = 'APPROVED_PUBLIC' WHERE project_status IS NULL")
                cursor.execute("UPDATE projects SET public_visibility = 1 WHERE public_visibility IS NULL")
                cursor.execute("UPDATE projects SET address = micro_market || ', Hyderabad' WHERE address IS NULL")

                # Ensure public_project_views view exists
                cursor.execute("""
                    CREATE VIEW IF NOT EXISTS public_project_views AS
                    SELECT 
                        p.id AS project_id,
                        p.name AS project_name,
                        p.developer AS developer_name,
                        p.promoter_legal_entity,
                        p.rera_id,
                        p.micro_market,
                        p.address,
                        p.latitude,
                        p.longitude,
                        p.sanctioning_authority,
                        p.approved_towers,
                        p.registered_handover_date,
                        p.handover_year,
                        p.total_acres,
                        p.clubhouse_sqft,
                        p.open_space_pct,
                        p.hero_image_url,
                        p.gallery_images,
                        p.walkthrough_video_url,
                        p.brochure_pdf_url,
                        p.master_plan_url,
                        p.cost_sheet_pdf_url,
                        p.site_progress_photos,
                        p.overall_risk_level,
                        p.next_review_at,
                        p.project_status,
                        p.public_visibility
                    FROM projects p
                    WHERE p.project_status = 'APPROVED_PUBLIC'
                      AND p.public_visibility = 1
                      AND NOT EXISTS (
                          SELECT 1 FROM risk_flags rf 
                          WHERE rf.project_id = p.id 
                            AND rf.severity = 'BLOCKING_HIGH' 
                            AND rf.resolved_at IS NULL
                      );
                """)

                cursor.execute("PRAGMA table_info(units)")
                unit_cols = [c[1] for c in cursor.fetchall()]
                if unit_cols and "floor_plan_image_url" not in unit_cols:
                    cursor.execute("ALTER TABLE units ADD COLUMN floor_plan_image_url TEXT")

                conn.commit()
                
                # Ensure all verified inventory, verification records and latest seed data are synced
                self.seed_database(conn)
                self.seed_verification_records(conn)
                self.seed_telemetry_and_buyers(conn)

    def seed_database(self, conn) -> None:
        from four_corner.media import find_project_media
        for prj in PROJECTS_DATA:
            m = find_project_media(prj["name"])
            hero = m.get("hero_image_url")
            gallery = json.dumps(m.get("gallery_images", []))
            video = m.get("walkthrough_video_url")
            drone = m.get("drone_footage_url")
            brochure = m.get("brochure_pdf_url")
            plan = m.get("master_plan_url")
            cost = m.get("cost_sheet_pdf_url")
            site_p = json.dumps(m.get("site_progress_photos", []))

            conn.execute(
                """
                INSERT OR REPLACE INTO projects (
                    id, name, developer, rera_id, micro_market, promoter_legal_entity,
                    sanctioning_authority, approved_towers, registered_handover_date,
                    handover_year, status, escrow_compliant, litigations_reported,
                    quarterly_compliance_up_to_date, total_acres, clubhouse_sqft, open_space_pct,
                    hero_image_url, gallery_images, walkthrough_video_url, drone_footage_url,
                    brochure_pdf_url, master_plan_url, cost_sheet_pdf_url, site_progress_photos
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prj["id"], prj["name"], prj["developer"], prj["rera_id"],
                    prj["micro_market"], prj["promoter_legal_entity"],
                    prj["sanctioning_authority"], prj["approved_towers"],
                    prj["registered_handover_date"], prj["handover_year"],
                    prj["status"], prj["escrow_compliant"],
                    prj["litigations_reported"], prj["quarterly_compliance_up_to_date"],
                    prj["total_acres"], prj["clubhouse_sqft"], prj["open_space_pct"],
                    hero, gallery, video, drone, brochure, plan, cost, site_p
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
                u_floor_plan = (m.get("unit_floor_plans") or {}).get(u["id"]) or (m.get("unit_floor_plans") or {}).get("default")

                conn.execute(
                    """
                    INSERT OR REPLACE INTO units (
                        id, project_id, tower, floor, bhk, facing, is_corner_unit,
                        super_built_up_sqft, carpet_area_sqft, balcony_sqft, balcony_facing,
                        has_morning_sunlight, base_rate_per_sqft, floor_rise_charges,
                        corner_premium_charges, clubhouse_charges, car_parking_slots,
                        car_parking_charges, infra_charges, total_out_the_door_inr, total_price_cr,
                        floor_plan_image_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        u["id"], prj["id"], u["tower"], u["floor"], u["bhk"], u["facing"],
                        u["is_corner_unit"], u["super_built_up_sqft"], u["carpet_area_sqft"],
                        u["balcony_sqft"], u["balcony_facing"], u["has_morning_sunlight"],
                        u["base_rate_per_sqft"], floor_rise, corner_prem, clubhouse,
                        2, car_parking, infra, total_inr, total_cr,
                        u_floor_plan
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

    def seed_verification_records(self, conn) -> None:
        """Seed baseline verification records, parcels, and reverification schedules for seeded projects."""
        import uuid
        from datetime import datetime, timedelta

        cur = conn.cursor()
        cur.execute("SELECT id, name, developer, rera_id, micro_market, sanctioning_authority, total_acres FROM projects")
        projects = cur.fetchall()

        now_str = datetime.now().isoformat()
        next_month = (datetime.now() + timedelta(days=90)).isoformat()

        for p in projects:
            p_id = p["id"] if isinstance(p, dict) or hasattr(p, "keys") else p[0]
            p_name = p["name"] if isinstance(p, dict) or hasattr(p, "keys") else p[1]
            p_dev = p["developer"] if isinstance(p, dict) or hasattr(p, "keys") else p[2]
            p_rera = p["rera_id"] if isinstance(p, dict) or hasattr(p, "keys") else p[3]
            p_market = p["micro_market"] if isinstance(p, dict) or hasattr(p, "keys") else p[4]
            p_auth = p["sanctioning_authority"] if isinstance(p, dict) or hasattr(p, "keys") else p[5]
            p_acres = p["total_acres"] if isinstance(p, dict) or hasattr(p, "keys") else p[6]

            # Check if verification records already exist for this project
            cur.execute("SELECT COUNT(*) FROM verification_records WHERE project_id = ?", (p_id,))
            cnt_row = cur.fetchone()
            cnt = (cnt_row[0] if cnt_row else 0) or 0
            if cnt > 0:
                continue

            # 1. Land Parcel
            parcel_id = f"pcl_{uuid.uuid4().hex[:12]}"
            conn.execute(
                """
                INSERT OR IGNORE INTO project_land_parcels (
                    id, project_id, survey_number, subdivision_number, village, mandal, district,
                    land_extent_acres, geometry_confidence, verified_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (parcel_id, p_id, "41/2 & 41/3", "A", p_market, "Gandipet", "Rangareddy", p_acres or 5.0, "SURVEYED", now_str)
            )

            # 2. Baseline Field Verification Records
            categories = [
                ("IDENTITY", "project_identity", p_name, p_name, "PASSED", "LOW", "GOVT_PORTAL_MANUAL", "Audited against official builder filings"),
                ("TG_RERA", "rera_registration", p_rera, p_rera, "PASSED", "LOW", "GOVT_PORTAL_MANUAL", "Authenticated on rera.telangana.gov.in portal"),
                ("APPROVALS", "building_permission", p_auth or "GHMC", p_auth or "GHMC", "PASSED", "LOW", "GOVT_PORTAL_MANUAL", f"Sanction order verified under {p_auth}"),
                ("LAND_TITLE", "title_report", "Parent title chain verified", "Verified clean title", "PASSED_WITH_LIMITATIONS", "LOW", "LEGACY_IMPORTED", "30-year parent deed chain inspected; regular legal due diligence advised"),
                ("HYDRAA_SPATIAL_RISK", "spatial_screening", "Survey No 41/2", "SCREENING_CLEAR_WITHIN_AVAILABLE_DATA", "PASSED", "LOW", "SURVEYOR_CAD", "Cadastral lake FTL & buffer zone query clear within available HMDA 2031 map data"),
                ("UNIT_AREA", "carpet_area_usability", "Approved plan measurements", "Verified room-by-room", "PASSED", "LOW", "OCR_EXTRACTION", "Sanctioned architectural drawing carpet area verified"),
                ("PRICING", "cost_sheet", "Zero broker markup direct builder pricing", "Direct Developer Sheet", "PASSED", "LOW", "GOVT_PORTAL_MANUAL", "Unbundled builder cost sheet authenticated directly"),
                ("MEDIA", "visual_assets", "Authentic Developer Facade & Daylight Living Space", "CDN Verified", "PASSED", "LOW", "AUDITOR_PHYSICAL", "Vetted architectural elevation and sanctioned blueprints hosted on CDN"),
                ("COMMUTE", "peak_rush_hour_traffic", "Corridor commute to ADP Gachibowli", "Live corridor calculated", "PASSED", "LOW", "AUDITOR_PHYSICAL", "Rush-hour road matrix calculated with arterial bottleneck detection"),
            ]

            for cat, field, sub_val, ver_val, status, risk, src_type, notes in categories:
                rec_id = f"vrf_{uuid.uuid4().hex[:12]}"
                conn.execute(
                    """
                    INSERT INTO verification_records (
                        id, project_id, category, field_name, submitted_value, verified_value,
                        status, risk_level, source_type, checked_at, expires_at, reviewer_role, confidence_score, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (rec_id, p_id, cat, field, sub_val, ver_val, status, risk, src_type, now_str, next_month, "SUPER_ADMIN", 1.0, notes)
                )

            # 3. Reverification Schedule
            sched_id = f"rev_{uuid.uuid4().hex[:12]}"
            conn.execute(
                """
                INSERT OR IGNORE INTO reverification_schedule (
                    id, project_id, category, last_checked_at, next_check_at, reason, priority
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (sched_id, p_id, "TG_RERA", now_str, next_month, "QUARTERLY_RERA_FILING", "NORMAL")
            )

        conn.commit()

    def seed_telemetry_and_buyers(self, conn) -> None:
        """Seed rich realistic buyers, inquiries, and search events if database has low telemetry."""
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM search_events")
        row = cur.fetchone()
        cnt = (row[0] if row else 0) or 0
        if cnt >= 20:
            return

        import uuid
        from datetime import datetime, timezone, timedelta

        # 1. Seed Qualified Buyers
        seed_users = [
            ("usr_ananya_04", "ananya.reddy@apollohospitals.com", "Dr. Ananya Reddy", "+91 94401 23456", "Nallagandla", 2.6, 3.0, 92, "TRANSACTION_READY", json.dumps({"financial_readiness": 95, "decision_urgency": 90, "inventory_engagement": 90, "regulatory_awareness": 90, "market_velocity": 92})),
            ("usr_deepa_06", "deepa.s@amazon.com", "Deepa Sundaram", "+91 91234 56789", "Nallagandla", 2.4, 3.0, 84, "HIGH_INTENT", json.dumps({"financial_readiness": 85, "decision_urgency": 80, "inventory_engagement": 85, "regulatory_awareness": 85, "market_velocity": 82})),
            ("usr_vikram_01", "vikram.adiga@hyderabadtech.com", "Vikram Adiga", "+91 98490 12345", "Tellapur", 2.8, 3.0, 88, "TRANSACTION_READY", json.dumps({"financial_readiness": 90, "decision_urgency": 85, "inventory_engagement": 90, "regulatory_awareness": 85, "market_velocity": 90})),
            ("usr_priya_02", "priya.sharma@microsoft.com", "Priya Sharma", "+91 97012 34567", "Financial District", 3.2, 3.5, 82, "HIGH_INTENT", json.dumps({"financial_readiness": 85, "decision_urgency": 80, "inventory_engagement": 85, "regulatory_awareness": 80, "market_velocity": 80})),
            ("usr_rahul_03", "rahul.v@deloitte.com", "Rahul Varma", "+91 99887 65432", "Gachibowli", 2.1, 3.0, 76, "HIGH_INTENT", json.dumps({"financial_readiness": 80, "decision_urgency": 75, "inventory_engagement": 75, "regulatory_awareness": 75, "market_velocity": 75})),
            ("usr_suresh_07", "suresh.c@phoenixcorp.in", "Suresh Chukkapalli", "+91 98480 99887", "Kokapet", 5.5, 4.0, 85, "HIGH_INTENT", json.dumps({"financial_readiness": 95, "decision_urgency": 80, "inventory_engagement": 85, "regulatory_awareness": 85, "market_velocity": 80})),
            ("usr_karthik_05", "karthik.rao@google.com", "Karthik Rao", "+91 98665 43210", "Tellapur", 2.6, 3.0, 68, "ACTIVE_EVALUATOR", json.dumps({"financial_readiness": 70, "decision_urgency": 65, "inventory_engagement": 70, "regulatory_awareness": 70, "market_velocity": 65})),
            ("usr_neha_08", "neha.gupta@servicenow.com", "Neha Gupta", "+91 97000 11223", "Kollur", 1.9, 2.5, 72, "ACTIVE_EVALUATOR", json.dumps({"financial_readiness": 75, "decision_urgency": 70, "inventory_engagement": 70, "regulatory_awareness": 75, "market_velocity": 70})),
        ]
        for u in seed_users:
            conn.execute("""
                INSERT OR REPLACE INTO users (
                    id, email, name, phone, micro_market_pref, budget_max_cr, bhk_pref,
                    intent_score, buyer_tier, intent_breakdown
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, u)

        # 2. Get all projects so we generate search events for every single project
        cur.execute("SELECT id, name, micro_market FROM projects")
        all_projects = [dict(r) for r in cur.fetchall()]
        if not all_projects:
            all_projects = [{"id": p["id"], "name": p["name"], "micro_market": p["micro_market"]} for p in PROJECTS_DATA]

        now = datetime.now(timezone.utc)
        user_ids = [u[0] for u in seed_users]

        for p_idx, prj in enumerate(all_projects):
            p_name = prj["name"]
            m_market = prj.get("micro_market") or "Financial District"
            neighbor_names = [o["name"] for o in all_projects if o["name"] != p_name][:2]

            for s_i in range(12):
                days_ago = (s_i * 13 + p_idx * 7) % 7
                hours_ago = (s_i * 3 + p_idx) % 24
                search_time = (now - timedelta(days=days_ago, hours=hours_ago, minutes=s_i * 4)).isoformat()

                assigned_user = user_ids[(s_i + p_idx) % len(user_ids)] if s_i % 3 != 0 else None
                bhk = [2.5, 3.0, 3.0, 3.5, 4.0][(s_i + p_idx) % 5]
                facing = ["East", "North", "West", "North-East"][(s_i + p_idx) % 4]
                corner = 1 if (s_i + p_idx) % 2 == 0 else 0
                morning = 1 if (s_i + p_idx) % 3 != 0 else 0
                min_b = [1.2, 1.5, 1.8, 2.0][s_i % 4]
                max_b = [2.2, 2.8, 3.2, 4.5][s_i % 4]

                if s_i % 2 == 0 and neighbor_names:
                    returned_names = f"{p_name},{neighbor_names[0]}"
                else:
                    returned_names = p_name

                conn.execute("""
                    INSERT OR REPLACE INTO search_events (
                        id, user_id, timestamp, micro_market, max_budget_cr, min_budget_cr,
                        bhk, facing, corner_only, morning_sunlight_only, ready_by_year,
                        min_carpet_sqft, results_count, unit_ids_returned, project_names_returned
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), assigned_user, search_time, m_market, max_b, min_b,
                    bhk, facing, corner, morning, 2026, 1400, 4, "", returned_names
                ))

        sample_inquiries = [
            ("usr_ananya_04", "Aparna Sarovar Zenith", "Pricing & Unit Breakdown", "Interested in 3 BHK Tower C East-facing corner unit on 12th floor with morning sunlight. Requesting complete out-the-door breakdown.", "in_progress"),
            ("usr_deepa_06", "Aparna Sarovar Zenith", "Floor Plan & Legal Verification", "Looking for verified carpet efficiency and approved towers for 3 BHK unit.", "new"),
            ("usr_vikram_01", "My Home Akrida", "Site Visit Request", "Would like to schedule weekend walkthrough for 3 BHK corner unit.", "scheduled"),
            ("usr_priya_02", "Aparna Zenon", "Pricing Sheet", "Requesting infrastructure and clubhouse charges clarification.", "contacted"),
            ("usr_suresh_07", "SAS Crown", "Executive Penthouse Inquiry", "Evaluating 4 BHK sky villa with 3 car parkings.", "in_progress"),
            ("usr_rahul_03", "Candeur Lakescape", "Carpet Efficiency Audit", "Please share verified TS-RERA carpet-to-super built-up ratio document.", "new"),
            ("usr_neha_08", "Honer Signatis", "Floor Rise Inclusions", "Need full break-up of floor rise and corner charges.", "new"),
        ]
        for user_id, prj_name, inq_type, msg, status in sample_inquiries:
            try:
                conn.execute("""
                    INSERT INTO user_inquiries (
                        user_id, unit_id, project_name, inquiry_type, user_message, status
                    ) VALUES (?, NULL, ?, ?, ?, ?)
                """, (user_id, prj_name, inq_type, msg, status))
            except Exception:
                pass

        conn.commit()

    def search_properties(
        self,
        project_name: Optional[str] = None,
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
                u.total_out_the_door_inr,
                p.hero_image_url,
                p.walkthrough_video_url,
                p.drone_footage_url,
                p.brochure_pdf_url,
                p.master_plan_url,
                u.floor_plan_image_url
            FROM units u
            JOIN projects p ON u.project_id = p.id
            WHERE p.project_status = 'APPROVED_PUBLIC'
              AND p.public_visibility = 1
              AND NOT EXISTS (
                  SELECT 1 FROM risk_flags rf 
                  WHERE rf.project_id = p.id 
                    AND rf.severity = 'BLOCKING_HIGH' 
                    AND rf.resolved_at IS NULL
              )
        """
        params = []

        if project_name:
            clean_proj = project_name.strip()
            query += " AND (LOWER(p.name) LIKE LOWER(?) OR LOWER(?) LIKE '%' || LOWER(p.name) || '%')"
            params.extend([f"%{clean_proj}%", clean_proj])
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
                  AND p.project_status = 'APPROVED_PUBLIC'
                  AND p.public_visibility = 1
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
                WHERE (LOWER(rera_id) = LOWER(?) OR LOWER(name) LIKE LOWER(?))
                  AND project_status = 'APPROVED_PUBLIC'
                  AND public_visibility = 1
                """,
                (project_or_rera.strip(), f"%{project_or_rera.strip()}%")
            )
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    def get_project_media(self, project_id_or_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve media assets stored in database for a project."""
        clean_target = project_id_or_name.strip()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, developer, micro_market, rera_id,
                       hero_image_url, gallery_images, walkthrough_video_url, drone_footage_url,
                       brochure_pdf_url, master_plan_url, cost_sheet_pdf_url, site_progress_photos
                FROM projects
                WHERE (LOWER(id) = LOWER(?) OR LOWER(name) LIKE LOWER(?) OR LOWER(rera_id) = LOWER(?))
                  AND project_status = 'APPROVED_PUBLIC'
                  AND public_visibility = 1
                LIMIT 1
                """,
                (clean_target, f"%{clean_target}%", clean_target)
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
                  AND p.project_status = 'APPROVED_PUBLIC'
                  AND p.public_visibility = 1
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
