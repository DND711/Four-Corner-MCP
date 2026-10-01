"""
OAuth 2.0 Authorization Server and User Management for Four Corner.
Enables user login, buyer data collection, and token authentication for ChatGPT and AI assistants.
"""

import time
import secrets
import sqlite3
from typing import Optional, Dict, Any, Tuple
from four_corner.db.database import Database

TOKEN_LIFETIME_SECONDS = 30 * 24 * 3600  # 30 days
CODE_LIFETIME_SECONDS = 600  # 10 minutes


def get_or_create_user(
    db: Database,
    email: str,
    name: str,
    phone: Optional[str] = None,
    micro_market_pref: Optional[str] = None,
    budget_max_cr: Optional[float] = None,
    bhk_pref: Optional[float] = None,
) -> Dict[str, Any]:
    """Create or update a registered buyer profile in Four Corner."""
    email = email.strip().lower()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        
        if row:
            user_id = row["id"]
            cursor.execute(
                """
                UPDATE users
                SET name = COALESCE(?, name),
                    phone = COALESCE(?, phone),
                    micro_market_pref = COALESCE(?, micro_market_pref),
                    budget_max_cr = COALESCE(?, budget_max_cr),
                    bhk_pref = COALESCE(?, bhk_pref),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (name, phone, micro_market_pref, budget_max_cr, bhk_pref, user_id)
            )
        else:
            user_id = f"usr_{secrets.token_hex(8)}"
            cursor.execute(
                """
                INSERT INTO users (
                    id, email, name, phone, micro_market_pref, budget_max_cr, bhk_pref
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, email, name, phone, micro_market_pref, budget_max_cr, bhk_pref)
            )
        conn.commit()

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return dict(cursor.fetchone())


def create_authorization_code(
    db: Database,
    client_id: str,
    user_id: str,
    redirect_uri: str,
    scope: str = "openid profile email"
) -> str:
    """Generate and store an OAuth 2.0 authorization code."""
    code = f"fc_code_{secrets.token_urlsafe(32)}"
    expires_at = int(time.time()) + CODE_LIFETIME_SECONDS

    with db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO oauth_codes (code, client_id, user_id, redirect_uri, scope, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (code, client_id, user_id, redirect_uri, scope, expires_at)
        )
        conn.commit()
    return code


def exchange_code_for_token(
    db: Database,
    code: str,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    redirect_uri: Optional[str] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Exchange an authorization code for an OAuth access token."""
    now = int(time.time())
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM oauth_codes WHERE code = ?", (code,))
        row = cursor.fetchone()

        if not row:
            return None, "Invalid or expired authorization code"

        if row["expires_at"] < now:
            cursor.execute("DELETE FROM oauth_codes WHERE code = ?", (code,))
            conn.commit()
            return None, "Authorization code has expired"

        user_id = row["user_id"]
        scope = row["scope"] or "openid profile email"

        # Generate access token
        access_token = f"fc_tok_{secrets.token_urlsafe(32)}"
        refresh_token = f"fc_ref_{secrets.token_urlsafe(32)}"
        expires_at = now + TOKEN_LIFETIME_SECONDS

        cursor.execute(
            """
            INSERT INTO oauth_tokens (token, refresh_token, client_id, user_id, scope, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (access_token, refresh_token, client_id or row["client_id"], user_id, scope, expires_at)
        )
        # Delete used code (single use)
        cursor.execute("DELETE FROM oauth_codes WHERE code = ?", (code,))
        conn.commit()

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()

        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": TOKEN_LIFETIME_SECONDS,
            "refresh_token": refresh_token,
            "scope": scope,
            "user": dict(user_row) if user_row else None
        }, None


def validate_access_token(db: Database, token: str) -> Optional[Dict[str, Any]]:
    """Validate a bearer token and return the associated user profile."""
    if not token:
        return None
    
    # Strip 'Bearer ' if present
    if token.lower().startswith("bearer "):
        token = token[7:].strip()

    now = int(time.time())
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT u.* FROM oauth_tokens t
            JOIN users u ON t.user_id = u.id
            WHERE t.token = ? AND t.expires_at > ?
            """,
            (token, now)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def save_user_favorite(db: Database, user_id: str, unit_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
    """Save a property unit to the authenticated user's portfolio."""
    with db.get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO user_saved_units (user_id, unit_id, notes, saved_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, unit_id, notes)
        )
        conn.commit()
    return {"status": "success", "message": f"Unit {unit_id} saved to your buyer portfolio"}


def submit_developer_inquiry(
    db: Database,
    user_id: str,
    project_name: str,
    inquiry_type: str,
    unit_id: Optional[str] = None,
    user_message: Optional[str] = None
) -> Dict[str, Any]:
    """Submit a verified direct-developer inquiry or site visit request with zero broker markup."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_inquiries (user_id, unit_id, project_name, inquiry_type, user_message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, unit_id, project_name, inquiry_type, user_message)
        )
        inquiry_id = cursor.lastrowid
        conn.commit()
    return {
        "status": "success",
        "inquiry_id": inquiry_id,
        "message": f"Direct developer request for '{project_name}' registered. Our verified buyer desk will connect with zero broker commission."
    }


def render_login_page(client_id: str, redirect_uri: str, state: Optional[str] = None) -> str:
    """Render a premium branded OAuth login & registration HTML page for Four Corner."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Connect Four Corner with ChatGPT</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background-color: #0B0F17;
      color: #F8FAFC;
    }}
  </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4 bg-[#0B0F17]">
  <div class="w-full max-w-md bg-[#131B2A] border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
    
    <!-- Header with Four Corner 2x2 Logo -->
    <div class="flex items-center gap-3 mb-6">
      <div class="w-10 h-10 rounded-xl bg-black border border-slate-700 flex items-center justify-center">
        <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="3" width="7" height="7" rx="1.5" />
          <rect x="14" y="3" width="7" height="7" rx="1.5" fill="#10B981" stroke="#10B981" />
          <rect x="14" y="14" width="7" height="7" rx="1.5" />
          <rect x="3" y="14" width="7" height="7" rx="1.5" />
        </svg>
      </div>
      <div>
        <h1 class="text-lg font-bold text-white tracking-tight">Four Corner</h1>
        <p class="text-xs text-slate-400">Verified Real Estate Intelligence</p>
      </div>
    </div>

    <!-- Purpose / Explanation -->
    <div class="mb-6 p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
      <div class="flex items-start gap-2.5">
        <span class="text-emerald-400 text-sm mt-0.5">✓</span>
        <p class="text-xs text-slate-300 leading-relaxed">
          Sign in to connect Four Corner with <strong class="text-white">ChatGPT</strong>. Save your search criteria, compare floor plans, and access direct developer pricing with zero broker commission.
        </p>
      </div>
    </div>

    <!-- Form -->
    <form method="POST" action="/oauth/authorize" class="space-y-4">
      <input type="hidden" name="client_id" value="{client_id}">
      <input type="hidden" name="redirect_uri" value="{redirect_uri}">
      <input type="hidden" name="state" value="{state or ''}">

      <div>
        <label class="block text-xs font-semibold text-slate-300 mb-1.5">Full Name *</label>
        <input type="text" name="name" required placeholder="e.g. Sahith Thota"
          class="w-full bg-[#0B0F17] border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition">
      </div>

      <div>
        <label class="block text-xs font-semibold text-slate-300 mb-1.5">Email Address *</label>
        <input type="email" name="email" required placeholder="you@example.com"
          class="w-full bg-[#0B0F17] border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition">
      </div>

      <div>
        <label class="block text-xs font-semibold text-slate-300 mb-1.5">Phone Number (Optional for WhatsApp updates)</label>
        <input type="tel" name="phone" placeholder="+91 98765 43210"
          class="w-full bg-[#0B0F17] border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition">
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1.5">Preferred Area</label>
          <select name="micro_market_pref"
            class="w-full bg-[#0B0F17] border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-500 transition">
            <option value="Kokapet">Kokapet</option>
            <option value="Financial District">Financial District</option>
            <option value="Tellapur">Tellapur</option>
            <option value="Narsingi">Narsingi</option>
            <option value="Gachibowli">Gachibowli</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-300 mb-1.5">Max Budget</label>
          <select name="budget_max_cr"
            class="w-full bg-[#0B0F17] border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-emerald-500 transition">
            <option value="1.5">₹1.50 Cr</option>
            <option value="2.0">₹2.00 Cr</option>
            <option value="2.5">₹2.50 Cr</option>
            <option value="3.5">₹3.50 Cr</option>
            <option value="5.0">₹5.00+ Cr</option>
          </select>
        </div>
      </div>

      <div class="pt-2">
        <button type="submit"
          class="w-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold py-3 px-4 rounded-xl text-sm transition shadow-lg shadow-emerald-500/20 cursor-pointer flex items-center justify-center gap-2">
          <span>Authorize & Connect with ChatGPT</span>
          <span>→</span>
        </button>
      </div>
    </form>

    <div class="mt-5 text-center">
      <p class="text-[11px] text-slate-500">
        By connecting, you agree to Four Corner's zero-broker buyer policy. We never sell your number to telemarketers.
      </p>
    </div>

  </div>
</body>
</html>
"""
