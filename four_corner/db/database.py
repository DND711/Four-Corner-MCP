"""
Database connection, initialization, and query engine for Four Corner.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional

from four_corner.config import DEFAULT_DB_PATH, DB_DIR
from four_corner.db.seed_data import PROJECTS_DATA


class Database:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_database(self) -> None:
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
            
            # Check if seeded
            cursor.execute("SELECT COUNT(*) FROM projects")
            count = cursor.fetchone()[0]
            if count == 0:
                self.seed_database(conn)


    def seed_database(self, conn: sqlite3.Connection) -> None:
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
                for room in u.get("rooms", []):
                    conn.execute(
                        """
                        INSERT INTO unit_rooms (unit_id, room_name, dimensions_feet, carpet_sqft, facing)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (u["id"], room[0], room[1], room[2], room[3])
                    )

                # Insert balconies
                for balc in u.get("balconies", []):
                    conn.execute(
                        """
                        INSERT INTO unit_balconies (unit_id, balcony_name, dimensions_feet, orientation, morning_sunlight)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (u["id"], balc[0], balc[1], balc[2], balc[3])
                    )

            # Insert commutes
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
                ROUND((CAST(u.carpet_area_sqft AS REAL) / u.super_built_up_sqft) * 100.0, 1) as usable_efficiency_pct,
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
                    ROUND((CAST(u.carpet_area_sqft AS REAL) / u.super_built_up_sqft) * 100.0, 1) as usable_efficiency_pct
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
                query += " AND LOWER(c.destination_hub) LIKE LOWER(?)"
                params.append(f"%{destination_hub.strip()}%")

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

