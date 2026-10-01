-- Four Corner Real Estate Intelligence Schema

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    developer TEXT NOT NULL,
    rera_id TEXT UNIQUE NOT NULL,
    micro_market TEXT NOT NULL,
    promoter_legal_entity TEXT NOT NULL,
    sanctioning_authority TEXT NOT NULL,
    approved_towers INTEGER NOT NULL,
    registered_handover_date TEXT NOT NULL,
    handover_year INTEGER NOT NULL,
    status TEXT NOT NULL,
    escrow_compliant INTEGER NOT NULL DEFAULT 1,
    litigations_reported INTEGER NOT NULL DEFAULT 0,
    quarterly_compliance_up_to_date INTEGER NOT NULL DEFAULT 1,
    total_acres REAL,
    clubhouse_sqft INTEGER,
    open_space_pct REAL
);

CREATE TABLE IF NOT EXISTS units (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    tower TEXT NOT NULL,
    floor INTEGER NOT NULL,
    bhk REAL NOT NULL,
    facing TEXT NOT NULL,
    is_corner_unit INTEGER NOT NULL DEFAULT 0,
    super_built_up_sqft INTEGER NOT NULL,
    carpet_area_sqft INTEGER NOT NULL,
    balcony_sqft INTEGER NOT NULL,
    balcony_facing TEXT NOT NULL,
    has_morning_sunlight INTEGER NOT NULL DEFAULT 0,
    base_rate_per_sqft INTEGER NOT NULL,
    floor_rise_charges INTEGER NOT NULL DEFAULT 0,
    corner_premium_charges INTEGER NOT NULL DEFAULT 0,
    clubhouse_charges INTEGER NOT NULL DEFAULT 400000,
    car_parking_slots INTEGER NOT NULL DEFAULT 2,
    car_parking_charges INTEGER NOT NULL DEFAULT 600000,
    infra_charges INTEGER NOT NULL DEFAULT 350000,
    total_out_the_door_inr INTEGER NOT NULL,
    total_price_cr REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS unit_rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id TEXT NOT NULL REFERENCES units(id),
    room_name TEXT NOT NULL,
    dimensions_feet TEXT NOT NULL,
    carpet_sqft REAL NOT NULL,
    facing TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS unit_balconies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id TEXT NOT NULL REFERENCES units(id),
    balcony_name TEXT NOT NULL,
    dimensions_feet TEXT NOT NULL,
    orientation TEXT NOT NULL,
    morning_sunlight INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS commute_corridors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES projects(id),
    destination_hub TEXT NOT NULL,
    distance_km REAL NOT NULL,
    non_peak_mins INTEGER NOT NULL,
    rush_hour_morning_mins INTEGER NOT NULL,
    rush_hour_evening_mins INTEGER NOT NULL,
    primary_corridor TEXT NOT NULL,
    key_intersections TEXT NOT NULL,
    congestion_warning TEXT
);

CREATE INDEX IF NOT EXISTS idx_units_project ON units(project_id);
CREATE INDEX IF NOT EXISTS idx_units_price ON units(total_price_cr);
CREATE INDEX IF NOT EXISTS idx_units_bhk ON units(bhk);
CREATE INDEX IF NOT EXISTS idx_units_carpet ON units(carpet_area_sqft);
CREATE INDEX IF NOT EXISTS idx_projects_market ON projects(micro_market);
CREATE INDEX IF NOT EXISTS idx_commute ON commute_corridors(project_id, destination_hub);
