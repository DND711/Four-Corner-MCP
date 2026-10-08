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
    open_space_pct REAL,
    verification_status TEXT DEFAULT 'Verified',
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
    site_progress_photos TEXT,
    address TEXT,
    promoter_id TEXT,
    district TEXT DEFAULT 'Hyderabad',
    mandal TEXT,
    village TEXT,
    boundary_geometry TEXT,
    project_status TEXT NOT NULL DEFAULT 'APPROVED_PUBLIC',
    overall_risk_level TEXT NOT NULL DEFAULT 'LOW',
    public_visibility INTEGER NOT NULL DEFAULT 1,
    next_review_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS units (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    tower TEXT NOT NULL,
    floor INTEGER NOT NULL,
    bhk REAL NOT NULL,
    facing TEXT NOT NULL,
    is_corner_unit INTEGER NOT NULL DEFAULT 0,
    floor_plan_image_url TEXT,
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
    user_id TEXT NOT NULL REFERENCES users(id),
    redirect_uri TEXT NOT NULL,
    scope TEXT,
    code_challenge TEXT,
    code_challenge_method TEXT,
    expires_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS oauth_tokens (
    token TEXT PRIMARY KEY,
    refresh_token TEXT UNIQUE,
    client_id TEXT NOT NULL,
    user_id TEXT NOT NULL REFERENCES users(id),
    scope TEXT,
    expires_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS user_saved_units (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id),
    unit_id TEXT NOT NULL REFERENCES units(id),
    notes TEXT,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, unit_id)
);

CREATE TABLE IF NOT EXISTS user_inquiries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id),
    unit_id TEXT REFERENCES units(id),
    project_name TEXT NOT NULL,
    inquiry_type TEXT NOT NULL,
    user_message TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT REFERENCES users(id),
    tool_name TEXT NOT NULL,
    query_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
    user_id TEXT,
    timestamp TEXT,
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

-- ============================================================================
-- Enterprise Human-in-the-Loop Property Verification Entities
-- ============================================================================

-- 1. Project Land Parcels & Survey Numbers
CREATE TABLE IF NOT EXISTS project_land_parcels (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    survey_number TEXT NOT NULL,
    subdivision_number TEXT,
    village TEXT NOT NULL,
    mandal TEXT NOT NULL,
    district TEXT NOT NULL,
    land_extent_acres REAL,
    geometry TEXT,
    source_document_id TEXT,
    geometry_confidence TEXT DEFAULT 'PROVISIONAL',
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Verification Documents (Evidence Vault)
CREATE TABLE IF NOT EXISTS verification_documents (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    document_type TEXT NOT NULL,
    file_url TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    issuer TEXT,
    document_date TEXT,
    uploaded_by TEXT NOT NULL,
    extracted_text TEXT,
    extraction_confidence REAL DEFAULT 0.0,
    review_status TEXT NOT NULL DEFAULT 'PENDING',
    access_scope TEXT NOT NULL DEFAULT 'INTERNAL_ONLY',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Field-Level Verification Records
CREATE TABLE IF NOT EXISTS verification_records (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    unit_id TEXT REFERENCES units(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    field_name TEXT NOT NULL,
    submitted_value TEXT NOT NULL,
    verified_value TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    risk_level TEXT NOT NULL DEFAULT 'UNKNOWN',
    source_type TEXT NOT NULL,
    source_url TEXT,
    source_document_id TEXT REFERENCES verification_documents(id),
    source_date TEXT,
    checked_at TIMESTAMP,
    expires_at TIMESTAMP,
    reviewer_id TEXT,
    reviewer_role TEXT,
    confidence_score REAL DEFAULT 1.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Risk Flags
CREATE TABLE IF NOT EXISTS risk_flags (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    risk_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT NOT NULL,
    evidence_id TEXT REFERENCES verification_documents(id),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    resolved_by TEXT
);

-- 5. Audit Tasks
CREATE TABLE IF NOT EXISTS audit_tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    assigned_to TEXT,
    assigned_role TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'TODO',
    due_at TIMESTAMP,
    completed_at TIMESTAMP,
    reviewer_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Verification Events (Immutable Audit Log)
CREATE TABLE IF NOT EXISTS verification_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT
);

-- 7. Re-Verification Schedule
CREATE TABLE IF NOT EXISTS reverification_schedule (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    last_checked_at TIMESTAMP,
    next_check_at TIMESTAMP NOT NULL,
    reason TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'NORMAL'
);

CREATE INDEX IF NOT EXISTS idx_parcels_project ON project_land_parcels(project_id);
CREATE INDEX IF NOT EXISTS idx_vdocs_project ON verification_documents(project_id);
CREATE INDEX IF NOT EXISTS idx_vrecords_project ON verification_records(project_id, category);
CREATE INDEX IF NOT EXISTS idx_rflags_project ON risk_flags(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON audit_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON audit_tasks(status, assigned_role);
CREATE INDEX IF NOT EXISTS idx_vevents_project ON verification_events(project_id);
CREATE INDEX IF NOT EXISTS idx_reverify_next ON reverification_schedule(next_check_at);

-- 8. Restricted Public Database View
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


