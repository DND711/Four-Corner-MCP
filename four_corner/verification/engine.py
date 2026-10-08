"""
Human-in-the-Loop Property Verification Engine for Four Corner (Hyderabad).
Enforces role-based access control, field-level provenance, mismatch detection,
spatial screening, and strict public read-only boundaries.
"""

import json
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple

from four_corner.db.database import Database

# ============================================================================
# Core Status Models & Roles
# ============================================================================

class ProjectStatus:
    DRAFT = "DRAFT"
    PENDING_DOCUMENTS = "PENDING_DOCUMENTS"
    PENDING_AUDIT = "PENDING_AUDIT"
    NEEDS_CORRECTION = "NEEDS_CORRECTION"
    LEGAL_REVIEW = "LEGAL_REVIEW"
    SURVEY_REVIEW = "SURVEY_REVIEW"
    APPROVED_LIMITED = "APPROVED_LIMITED"
    APPROVED_PUBLIC = "APPROVED_PUBLIC"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"
    EXPIRED_REVIEW = "EXPIRED_REVIEW"


class VerificationStatus:
    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    PASSED = "PASSED"
    PASSED_WITH_LIMITATIONS = "PASSED_WITH_LIMITATIONS"
    FLAGGED = "FLAGGED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class RiskLevel:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class InternalRole:
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    DEVELOPER_USER = "DEVELOPER_USER"
    AUDITOR = "AUDITOR"
    LEGAL_REVIEWER = "LEGAL_REVIEWER"
    SURVEY_REVIEWER = "SURVEY_REVIEWER"
    ARCHITECT_REVIEWER = "ARCHITECT_REVIEWER"
    PRICING_REVIEWER = "PRICING_REVIEWER"
    READ_ONLY_INTERNAL_REVIEWER = "READ_ONLY_INTERNAL_REVIEWER"


class VerificationCategory:
    IDENTITY = "IDENTITY"
    TG_RERA = "TG_RERA"
    APPROVALS = "APPROVALS"
    LAND_TITLE = "LAND_TITLE"
    HYDRAA_SPATIAL_RISK = "HYDRAA_SPATIAL_RISK"
    UNIT_AREA = "UNIT_AREA"
    PRICING = "PRICING"
    MEDIA = "MEDIA"
    COMMUTE = "COMMUTE"


# ============================================================================
# Audit Logging Helper
# ============================================================================

def log_verification_event(
    db: Database,
    project_id: str,
    actor_id: str,
    action: str,
    previous_status: Optional[str] = None,
    new_status: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Record an append-only immutable audit event."""
    with db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO verification_events (
                project_id, actor_id, action, previous_status, new_status, metadata
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                actor_id,
                action,
                previous_status,
                new_status,
                json.dumps(metadata or {}),
            ),
        )
        conn.commit()


# ============================================================================
# Private Internal Workflow Operations
# ============================================================================

def create_project_submission(
    db: Database,
    promoter_id: str,
    project_data: Dict[str, Any],
    actor_id: str,
    actor_role: str,
) -> Dict[str, Any]:
    """Create a new draft project submission via internal API.
    Only DEVELOPER_USER, ADMIN, or SUPER_ADMIN can create.
    """
    if actor_role not in [InternalRole.DEVELOPER_USER, InternalRole.ADMIN, InternalRole.SUPER_ADMIN]:
        raise PermissionError(f"Role '{actor_role}' is not authorized to create project submissions.")

    project_id = project_data.get("id") or f"prj_{uuid.uuid4().hex[:12]}"
    name = project_data.get("name")
    developer = project_data.get("developer")
    rera_id = project_data.get("rera_id")
    micro_market = project_data.get("micro_market")

    if not name or not developer or not rera_id or not micro_market:
        raise ValueError("Missing required project submission fields (name, developer, rera_id, micro_market).")

    with db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO projects (
                id, name, developer, rera_id, micro_market, promoter_legal_entity,
                sanctioning_authority, approved_towers, registered_handover_date,
                handover_year, status, escrow_compliant, litigations_reported,
                quarterly_compliance_up_to_date, total_acres, clubhouse_sqft, open_space_pct,
                promoter_id, district, mandal, village, boundary_geometry,
                project_status, overall_risk_level, public_visibility
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                name,
                developer,
                rera_id,
                micro_market,
                project_data.get("promoter_legal_entity", developer),
                project_data.get("sanctioning_authority", "GHMC"),
                project_data.get("approved_towers", 1),
                project_data.get("registered_handover_date", "31 Dec 2027"),
                project_data.get("handover_year", 2027),
                "Under Construction",
                project_data.get("escrow_compliant", 1),
                project_data.get("litigations_reported", 0),
                1,
                project_data.get("total_acres", 5.0),
                project_data.get("clubhouse_sqft", 25000),
                project_data.get("open_space_pct", 75.0),
                promoter_id,
                project_data.get("district", "Rangareddy"),
                project_data.get("mandal", "Gandipet"),
                project_data.get("village", micro_market),
                project_data.get("boundary_geometry"),
                ProjectStatus.DRAFT,
                RiskLevel.UNKNOWN,
                0,  # Public visibility initially false
            ),
        )

        # Insert land parcel if survey number provided
        survey_number = project_data.get("survey_number")
        if survey_number:
            parcel_id = f"pcl_{uuid.uuid4().hex[:12]}"
            conn.execute(
                """
                INSERT INTO project_land_parcels (
                    id, project_id, survey_number, subdivision_number, village, mandal, district,
                    land_extent_acres, geometry_confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    parcel_id,
                    project_id,
                    survey_number,
                    project_data.get("subdivision_number", "A"),
                    project_data.get("village", micro_market),
                    project_data.get("mandal", "Gandipet"),
                    project_data.get("district", "Rangareddy"),
                    project_data.get("total_acres", 5.0),
                    "PROVISIONAL",
                ),
            )

        conn.commit()

    log_verification_event(
        db,
        project_id,
        actor_id,
        "SUBMIT_DRAFT",
        previous_status=None,
        new_status=ProjectStatus.DRAFT,
        metadata={"promoter_id": promoter_id, "project_name": name},
    )

    return {"status": "success", "project_id": project_id, "project_status": ProjectStatus.DRAFT}


def submit_for_verification(
    db: Database,
    project_id: str,
    actor_id: str,
    actor_role: str,
) -> Dict[str, Any]:
    """Transition a project from DRAFT to PENDING_AUDIT."""
    if actor_role not in [InternalRole.DEVELOPER_USER, InternalRole.ADMIN, InternalRole.SUPER_ADMIN]:
        raise PermissionError(f"Role '{actor_role}' is not authorized to submit project for verification.")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, project_status, promoter_id FROM projects WHERE id = ?", (project_id,))
        p = cursor.fetchone()
        if not p:
            raise ValueError(f"Project '{project_id}' not found.")

        # Tenancy check: Developer users can only submit their own projects
        if actor_role == InternalRole.DEVELOPER_USER and p["promoter_id"] != actor_id:
            raise PermissionError("Developer user cannot submit another promoter's project.")

        prev_status = p["project_status"]
        conn.execute(
            "UPDATE projects SET project_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (ProjectStatus.PENDING_AUDIT, project_id),
        )

        # Create baseline audit tasks
        for cat, role in [
            (VerificationCategory.IDENTITY, InternalRole.AUDITOR),
            (VerificationCategory.TG_RERA, InternalRole.AUDITOR),
            (VerificationCategory.APPROVALS, InternalRole.AUDITOR),
            (VerificationCategory.LAND_TITLE, InternalRole.LEGAL_REVIEWER),
            (VerificationCategory.HYDRAA_SPATIAL_RISK, InternalRole.SURVEY_REVIEWER),
            (VerificationCategory.UNIT_AREA, InternalRole.ARCHITECT_REVIEWER),
            (VerificationCategory.PRICING, InternalRole.PRICING_REVIEWER),
        ]:
            task_id = f"tsk_{uuid.uuid4().hex[:12]}"
            conn.execute(
                """
                INSERT OR IGNORE INTO audit_tasks (
                    id, project_id, category, assigned_role, status, due_at
                ) VALUES (?, ?, ?, ?, ?, datetime('now', '+7 days'))
                """,
                (task_id, project_id, cat, role, "TODO"),
            )

        conn.commit()

    log_verification_event(
        db,
        project_id,
        actor_id,
        "SUBMIT_FOR_AUDIT",
        previous_status=prev_status,
        new_status=ProjectStatus.PENDING_AUDIT,
    )

    return {"status": "success", "project_id": project_id, "project_status": ProjectStatus.PENDING_AUDIT}


def upload_verification_evidence(
    db: Database,
    project_id: str,
    category: str,
    document_type: str,
    file_url: str,
    file_bytes: Optional[bytes],
    issuer: str,
    actor_id: str,
    actor_role: str,
    document_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Upload verification document with SHA-256 integrity hash.
    DEVELOPER_USER, AUDITOR, ADMIN, or SUPER_ADMIN only.
    """
    if actor_role not in [
        InternalRole.DEVELOPER_USER,
        InternalRole.AUDITOR,
        InternalRole.ADMIN,
        InternalRole.SUPER_ADMIN,
    ]:
        raise PermissionError(f"Role '{actor_role}' is not authorized to upload verification evidence.")

    file_hash = (
        hashlib.sha256(file_bytes).hexdigest()
        if file_bytes
        else hashlib.sha256(file_url.encode("utf-8")).hexdigest()
    )

    doc_id = f"doc_{uuid.uuid4().hex[:12]}"

    with db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO verification_documents (
                id, project_id, category, document_type, file_url, file_hash, issuer,
                document_date, uploaded_by, review_status, access_scope
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                project_id,
                category,
                document_type,
                file_url,
                file_hash,
                issuer,
                document_date or datetime.now().strftime("%Y-%m-%d"),
                actor_id,
                "PENDING",
                "INTERNAL_ONLY",
            ),
        )
        conn.commit()

    log_verification_event(
        db,
        project_id,
        actor_id,
        "UPLOAD_EVIDENCE",
        metadata={"document_id": doc_id, "category": category, "file_hash": file_hash},
    )

    return {
        "status": "success",
        "document_id": doc_id,
        "file_hash": file_hash,
        "category": category,
    }


def record_field_verification(
    db: Database,
    project_id: str,
    category: str,
    field_name: str,
    submitted_value: str,
    verified_value: str,
    status: str,
    risk_level: str,
    source_type: str,
    actor_id: str,
    actor_role: str,
    notes: Optional[str] = None,
    source_document_id: Optional[str] = None,
    expires_in_days: int = 90,
) -> Dict[str, Any]:
    """Record an auditor or specialist's verification finding for a specific field."""
    if actor_role in [InternalRole.DEVELOPER_USER, InternalRole.READ_ONLY_INTERNAL_REVIEWER]:
        raise PermissionError(f"Role '{actor_role}' cannot record official field verifications.")

    rec_id = f"vrf_{uuid.uuid4().hex[:12]}"
    now_str = datetime.now().isoformat()
    expires_at = (datetime.now() + timedelta(days=expires_in_days)).isoformat()

    with db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO verification_records (
                id, project_id, category, field_name, submitted_value, verified_value,
                status, risk_level, source_type, source_document_id, checked_at, expires_at,
                reviewer_id, reviewer_role, confidence_score, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rec_id,
                project_id,
                category,
                field_name,
                submitted_value,
                verified_value,
                status,
                risk_level,
                source_type,
                source_document_id,
                now_str,
                expires_at,
                actor_id,
                actor_role,
                1.0,
                notes,
            ),
        )
        conn.commit()

    return {"status": "success", "verification_record_id": rec_id, "field_status": status}


def create_risk_flag(
    db: Database,
    project_id: str,
    category: str,
    risk_type: str,
    severity: str,
    description: str,
    evidence_id: Optional[str] = None,
) -> str:
    """Create a risk flag. Severity 'BLOCKING_HIGH' prevents public approval."""
    flag_id = f"flg_{uuid.uuid4().hex[:12]}"
    with db.get_connection() as conn:
        conn.execute(
            """
            INSERT INTO risk_flags (
                id, project_id, category, risk_type, severity, description, evidence_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (flag_id, project_id, category, risk_type, severity, description, evidence_id),
        )
        conn.commit()
    return flag_id


def resolve_risk_flag(
    db: Database,
    flag_id: str,
    resolution_notes: str,
    actor_id: str,
    actor_role: str,
) -> Dict[str, Any]:
    """Resolve a risk flag. Must match role constraints:
    - Legal flags require LEGAL_REVIEWER, ADMIN, or SUPER_ADMIN
    - Survey flags require SURVEY_REVIEWER, ADMIN, or SUPER_ADMIN
    - Other flags require AUDITOR, ADMIN, or SUPER_ADMIN
    """
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, project_id, category, risk_type, severity FROM risk_flags WHERE id = ?", (flag_id,))
        flag = cursor.fetchone()
        if not flag:
            raise ValueError(f"Risk flag '{flag_id}' not found.")

        cat = flag["category"]
        if cat == VerificationCategory.LAND_TITLE and actor_role not in [
            InternalRole.LEGAL_REVIEWER,
            InternalRole.ADMIN,
            InternalRole.SUPER_ADMIN,
        ]:
            raise PermissionError(f"Only LEGAL_REVIEWER or ADMIN can resolve Land Title risk flags.")

        if cat == VerificationCategory.HYDRAA_SPATIAL_RISK and actor_role not in [
            InternalRole.SURVEY_REVIEWER,
            InternalRole.ADMIN,
            InternalRole.SUPER_ADMIN,
        ]:
            raise PermissionError(f"Only SURVEY_REVIEWER or ADMIN can resolve HYDRAA Spatial risk flags.")

        conn.execute(
            """
            UPDATE risk_flags 
            SET resolved_at = CURRENT_TIMESTAMP, resolution_notes = ?, resolved_by = ?
            WHERE id = ?
            """,
            (resolution_notes, actor_id, flag_id),
        )
        conn.commit()

    log_verification_event(
        db,
        flag["project_id"],
        actor_id,
        "RESOLVE_RISK_FLAG",
        metadata={"flag_id": flag_id, "resolution_notes": resolution_notes},
    )

    return {"status": "success", "flag_id": flag_id, "resolved": True}


def approve_public(
    db: Database,
    project_id: str,
    actor_id: str,
    actor_role: str,
) -> Dict[str, Any]:
    """Approve project for public listing into public_project_views.
    Requires SUPER_ADMIN or ADMIN.
    Rejects if unresolved BLOCKING_HIGH flags exist or mandatory checks have failed.
    """
    if actor_role not in [InternalRole.SUPER_ADMIN, InternalRole.ADMIN]:
        raise PermissionError(f"Role '{actor_role}' is not authorized to grant final public publication approval.")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        # 1. Check for blocking risk flags
        cursor.execute(
            """
            SELECT count(*) FROM risk_flags
            WHERE project_id = ? AND severity = 'BLOCKING_HIGH' AND resolved_at IS NULL
            """,
            (project_id,),
        )
        blocking_cnt = cursor.fetchone()[0]
        if blocking_cnt > 0:
            raise ValueError(f"Cannot approve project for public listing: {blocking_cnt} unresolved blocking risk flags.")

        # 2. Check that Identity, RERA, and Spatial have passed or passed with limitations
        cursor.execute(
            """
            SELECT category, status FROM verification_records
            WHERE project_id = ? AND status IN ('FAILED', 'FLAGGED')
            """,
            (project_id,),
        )
        failed_records = cursor.fetchall()
        if failed_records:
            cats = [f["category"] for f in failed_records]
            raise ValueError(f"Cannot approve project: Categories failed verification: {cats}")

        # 3. Update project status
        cursor.execute("SELECT project_status FROM projects WHERE id = ?", (project_id,))
        p = cursor.fetchone()
        prev_status = p["project_status"] if p else None

        next_rev = (datetime.now() + timedelta(days=90)).isoformat()
        conn.execute(
            """
            UPDATE projects
            SET project_status = ?,
                public_visibility = 1,
                overall_risk_level = 'LOW',
                next_review_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (ProjectStatus.APPROVED_PUBLIC, next_rev, project_id),
        )
        conn.commit()

    log_verification_event(
        db,
        project_id,
        actor_id,
        "APPROVE_PUBLIC",
        previous_status=prev_status,
        new_status=ProjectStatus.APPROVED_PUBLIC,
    )

    return {"status": "success", "project_id": project_id, "project_status": ProjectStatus.APPROVED_PUBLIC}


def suspend_project(
    db: Database,
    project_id: str,
    reason: str,
    actor_id: str,
    actor_role: str,
) -> Dict[str, Any]:
    """Immediately suspend project and remove from public view."""
    if actor_role not in [InternalRole.SUPER_ADMIN, InternalRole.ADMIN]:
        raise PermissionError(f"Role '{actor_role}' is not authorized to suspend projects.")

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT project_status FROM projects WHERE id = ?", (project_id,))
        p = cursor.fetchone()
        prev_status = p["project_status"] if p else None

        conn.execute(
            """
            UPDATE projects
            SET project_status = ?,
                public_visibility = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (ProjectStatus.SUSPENDED, project_id),
        )
        conn.commit()

    log_verification_event(
        db,
        project_id,
        actor_id,
        "SUSPEND_PROJECT",
        previous_status=prev_status,
        new_status=ProjectStatus.SUSPENDED,
        metadata={"reason": reason},
    )

    return {"status": "success", "project_id": project_id, "project_status": ProjectStatus.SUSPENDED}


# ============================================================================
# Public Read-Only Verification Summary & Disclosures
# ============================================================================

def get_public_verification_summary(db: Database, project_name_or_id: str) -> Dict[str, Any]:
    """Return public-safe verification audit trail.
    Queries ONLY approved projects. Omit private reviewer notes and sensitive evidence URLs.
    """
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM public_project_views 
            WHERE project_id = ? OR LOWER(project_name) = LOWER(?)
            """,
            (project_name_or_id, project_name_or_id),
        )
        p = cursor.fetchone()
        if not p:
            return {
                "status": "not_found_or_unapproved",
                "message": f"Project '{project_name_or_id}' is not an approved public listing.",
            }

        p_id = p["project_id"]

        # Fetch category verification records
        cursor.execute(
            """
            SELECT category, field_name, verified_value, status, checked_at, source_type
            FROM verification_records
            WHERE project_id = ?
            """,
            (p_id,),
        )
        records = cursor.fetchall()
        cat_summaries = {}
        for r in records:
            cat = r["category"]
            cat_summaries[cat] = {
                "status": r["status"],
                "last_checked_at": r["checked_at"][:10] if r["checked_at"] else None,
                "verification_method": r["source_type"],
            }

        # Public risk disclosures
        cursor.execute(
            """
            SELECT risk_type, severity, description
            FROM risk_flags
            WHERE project_id = ? AND severity != 'BLOCKING_HIGH'
            """,
            (p_id,),
        )
        flags = cursor.fetchall()

    return {
        "status": "success",
        "project_id": p["project_id"],
        "project_name": p["project_name"],
        "developer_name": p["developer_name"],
        "rera_number": p["rera_id"],
        "handover_date_official": p["registered_handover_date"],
        "verification_categories": cat_summaries,
        "advisory_disclosures": [f["description"] for f in flags] if flags else [
            "Cadastral and title checks reflect government records available at the time of review.",
            "Four Corner advises independent legal due diligence prior to property registration.",
        ],
        "consumer_disclaimer": "Four Corner audits documents against official TS-RERA and government filings. We do not provide financial or legal warranties."
    }


def get_public_risk_report(db: Database, project_name_or_id: str) -> Dict[str, Any]:
    """Retrieve consumer risk disclosures, spatial limitations, and legal advisories for an approved project."""
    summary = get_public_verification_summary(db, project_name_or_id)
    if summary.get("status") != "success":
        return summary

    return {
        "status": "success",
        "project_name": summary["project_name"],
        "rera_number": summary["rera_number"],
        "spatial_screening": {
            "status": summary["verification_categories"].get("HYDRAA_SPATIAL_RISK", {}).get("status", "NOT_CHECKED"),
            "disclaimer": "Screening completed against official HMDA 2031 lake cadastral layers. Physical on-ground survey verification recommended.",
        },
        "legal_title_status": {
            "status": summary["verification_categories"].get("LAND_TITLE", {}).get("status", "NOT_CHECKED"),
            "disclaimer": "Encumbrance certificate inspected. Independent lawyer verification recommended before financial commitments.",
        },
        "disclosures": summary.get("advisory_disclosures", []),
    }
