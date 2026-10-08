-- Four Corner Real Estate Intelligence — Supabase / PostgreSQL Schema

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
    open_space_pct REAL,
    verification_status TEXT DEFAULT 'Verified',
    project_status TEXT DEFAULT 'APPROVED_PUBLIC',
    overall_risk_level TEXT DEFAULT 'LOW',
    public_visibility INTEGER DEFAULT 1,
    next_review_at TIMESTAMP,
    promoter_id TEXT,
    district TEXT DEFAULT 'Hyderabad',
    mandal TEXT,
    village TEXT,
    boundary_geometry TEXT,
    address TEXT,
    updated_at TIMESTAMP,
    tagline TEXT,
    project_type TEXT,
    official_url TEXT,
    is_rera_registered INTEGER DEFAULT 1,
    total_units INTEGER,
    road_width_feet REAL,
    water_source TEXT,
    assigned_badge TEXT,
    auditor_id TEXT,
    latitude REAL,
    longitude REAL,
    construction_stage TEXT,
    road_condition TEXT,
    red_flag_notes TEXT,
    hero_image_url TEXT,
    gallery_images TEXT,
    walkthrough_video_url TEXT,
    drone_footage_url TEXT,
    brochure_pdf_url TEXT,
    master_plan_url TEXT,
    cost_sheet_pdf_url TEXT,
    site_progress_photos TEXT
);

CREATE TABLE IF NOT EXISTS units (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
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
    total_out_the_door_inr BIGINT NOT NULL,
    total_price_cr REAL NOT NULL,
    floor_plan_image_url TEXT
);

CREATE TABLE IF NOT EXISTS unit_rooms (
    id SERIAL PRIMARY KEY,
    unit_id TEXT NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    room_name TEXT NOT NULL,
    dimensions_feet TEXT NOT NULL,
    carpet_sqft REAL NOT NULL,
    facing TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS unit_balconies (
    id SERIAL PRIMARY KEY,
    unit_id TEXT NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    balcony_name TEXT NOT NULL,
    dimensions_feet TEXT NOT NULL,
    orientation TEXT NOT NULL,
    morning_sunlight INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS commute_corridors (
    id SERIAL PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    destination_hub TEXT NOT NULL,
    distance_km REAL NOT NULL,
    non_peak_mins INTEGER NOT NULL,
    rush_hour_morning_mins INTEGER NOT NULL,
    rush_hour_evening_mins INTEGER NOT NULL,
    primary_corridor TEXT NOT NULL,
    key_intersections TEXT NOT NULL,
    congestion_warning TEXT
);

-- ==========================================
-- User Accounts, OAuth 2.0 & Buyer Data
-- ==========================================

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT,
    micro_market_pref TEXT,
    budget_max_cr REAL,
    bhk_pref REAL,
    intent_score INTEGER NOT NULL DEFAULT 0,
    buyer_tier TEXT NOT NULL DEFAULT 'CASUAL_BROWSER',
    intent_breakdown TEXT,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS oauth_clients (
    client_id TEXT PRIMARY KEY,
    client_secret TEXT NOT NULL,
    client_name TEXT NOT NULL,
    redirect_uris TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS oauth_codes (
    code TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    redirect_uri TEXT NOT NULL,
    scope TEXT,
    code_challenge TEXT,
    code_challenge_method TEXT,
    expires_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS oauth_tokens (
    token TEXT PRIMARY KEY,
    refresh_token TEXT UNIQUE,
    client_id TEXT NOT NULL,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    scope TEXT,
    expires_at BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_saved_units (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    unit_id TEXT NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    notes TEXT,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, unit_id)
);

CREATE TABLE IF NOT EXISTS user_inquiries (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    unit_id TEXT REFERENCES units(id) ON DELETE SET NULL,
    project_name TEXT NOT NULL,
    inquiry_type TEXT NOT NULL,
    user_message TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_audit_logs (
    id SERIAL PRIMARY KEY,
    user_id TEXT REFERENCES users(id) ON DELETE SET NULL,
    tool_name TEXT NOT NULL,
    query_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for lightning-fast property search and buyer lookups
CREATE INDEX IF NOT EXISTS idx_units_project ON units(project_id);
CREATE INDEX IF NOT EXISTS idx_units_price ON units(total_price_cr);
CREATE INDEX IF NOT EXISTS idx_units_bhk ON units(bhk);
CREATE INDEX IF NOT EXISTS idx_units_carpet ON units(carpet_area_sqft);
CREATE INDEX IF NOT EXISTS idx_projects_market ON projects(micro_market);
CREATE INDEX IF NOT EXISTS idx_commute ON commute_corridors(project_id, destination_hub);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_oauth_tokens ON oauth_tokens(token);
CREATE INDEX IF NOT EXISTS idx_oauth_codes ON oauth_codes(code);

-- Search Events & Buyer Search Intelligence
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
