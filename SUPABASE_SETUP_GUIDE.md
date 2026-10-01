# Supabase PostgreSQL Setup Guide — Step-by-Step

> **Goal:** Connect a free, cloud-managed PostgreSQL database from [Supabase](https://supabase.com) to Four Corner so registered buyers, OAuth tokens, and inquiries are **100% persistent forever** across Render deployments.  
> **Estimated Time:** 3–5 minutes.  
> **Cost:** 100% Free (Supabase Free Tier).

---

## Step 1: Create Your Supabase Project (1 Minute)

1. Open [https://supabase.com](https://supabase.com) and click **"Start your project"** (Sign in with GitHub or email).
2. Click **"New Project"**.
3. Fill in the project details:
   - **Name:** `four-corner-mcp` (or any name you prefer)
   - **Database Password:** Enter a secure password (**Note: Save this password securely.** You will need it in Step 3).
   - **Region:** Select **`South Asia (Mumbai) - ap-south-1`** (closest to Hyderabad and fastest for Render).
   - **Pricing Plan:** **Free tier** ($0/month).
4. Click **"Create new project"**.
   *(Supabase will provision your database in about 1–2 minutes).*

---

## Step 2: Create the Database Tables in Supabase (1 Minute)

1. In your Supabase project dashboard, click on the **SQL Editor** icon in the left sidebar (looks like a terminal `>_`).
2. Click **"New query"**.
3. Copy and paste the entire SQL code below into the editor:

```sql
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
    open_space_pct REAL
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
    total_price_cr REAL NOT NULL
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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_units_project ON units(project_id);
CREATE INDEX IF NOT EXISTS idx_units_price ON units(total_price_cr);
CREATE INDEX IF NOT EXISTS idx_units_bhk ON units(bhk);
CREATE INDEX IF NOT EXISTS idx_projects_market ON projects(micro_market);
CREATE INDEX IF NOT EXISTS idx_commute ON commute_corridors(project_id, destination_hub);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

4. Click the green **"Run"** button (or press `Ctrl+Enter` / `Cmd+Enter`).
   You will see: `Success. No rows returned`. All tables and indexes are now created!

---

## Step 3: Copy Your Supabase Connection String (30 Seconds)

1. In your Supabase project dashboard, click the **Settings** gear icon (bottom-left) $\rightarrow$ click **Database**.
2. Scroll down to **Connection parameters** / **Connection string**.
3. Select the **URI** tab.
4. It looks like this:
   ```text
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
   ```
5. Click **Copy**, and replace `[YOUR-PASSWORD]` with the database password you chose in Step 1.
   *(Make sure to remove the brackets `[` and `]` around your password).*

---

## Step 4: Add `DATABASE_URL` in Render (1 Minute)

1. Open your [Render Dashboard](https://dashboard.render.com).
2. Click on your **`four-corner-mcp`** web service.
3. Click on the **Environment** tab in the left sub-menu.
4. Click **"Add Environment Variable"**:
   - **Key:** `DATABASE_URL`
   - **Value:** Paste your Supabase URI from Step 3:
     ```text
     postgresql://postgres.[PROJECT-REF]:YOUR_REAL_PASSWORD@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
     ```
5. Click **"Save Changes"**.
6. Render will automatically start a new deployment and connect directly to your Supabase database!

---

## Step 5: How to View Leads & Registered Buyers

Supabase gives you a built-in visual spreadsheet interface:
1. In your Supabase dashboard, click the **Table Editor** icon (table grid icon in left sidebar).
2. Click on the **`users`** table:
   - You will see every registered buyer in real time (Name, Email, Phone, Preferred Budget, Registration Timestamp).
3. Click on **`user_inquiries`**:
   - You will see all official builder inquiries and site visit requests.
4. Click on **`units`** or **`projects`**:
   - You can see or edit all property records directly in the web UI!
