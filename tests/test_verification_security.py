"""
Comprehensive Security and Human-in-the-Loop Verification Test Suite for Four Corner.
Tests access control rules, verification state transitions, spatial screening flags,
role permissions, and strict public read-only boundaries.
"""

import pytest
from four_corner.server import server, db
from four_corner.verification.engine import (
    ProjectStatus,
    VerificationStatus,
    RiskLevel,
    InternalRole,
    VerificationCategory,
    create_project_submission,
    submit_for_verification,
    upload_verification_evidence,
    record_field_verification,
    create_risk_flag,
    resolve_risk_flag,
    approve_public,
    suspend_project,
    get_public_verification_summary,
    get_public_risk_report,
)


@pytest.mark.anyio
async def test_public_mcp_cannot_perform_writes():
    """Verify that public MCP tools list contains NO write tools for projects/units/verification."""
    tools = await server.list_tools()
    tool_names = [t.name for t in tools]

    forbidden_tools = [
        "create_project",
        "edit_project",
        "delete_project",
        "create_unit",
        "edit_unit",
        "upload_evidence",
        "approve_project",
        "reject_project",
        "resolve_risk_flag",
        "save_favorite_unit",
        "write_database",
    ]
    for ft in forbidden_tools:
        assert ft not in tool_names, f"Forbidden write tool '{ft}' must not be exposed to public MCP."


@pytest.mark.anyio
async def test_public_mcp_cannot_access_unpublished_projects():
    """Verify that projects in DRAFT, PENDING_AUDIT, or REJECTED status never appear in public search."""
    # 1. Create a draft project
    import uuid
    rand_id = uuid.uuid4().hex[:8]
    draft = create_project_submission(
        db=db,
        promoter_id="promoter_test_99",
        project_data={
            "id": f"prj_secret_{rand_id}",
            "name": f"Secret Unapproved Villa {rand_id}",
            "developer": "Secret Developers",
            "rera_id": f"P0999_{rand_id}",
            "micro_market": "Kokapet",
        },
        actor_id="usr_dev_99",
        actor_role=InternalRole.DEVELOPER_USER,
    )
    assert draft["project_status"] == ProjectStatus.DRAFT

    # 2. Call public search_properties
    search_res = await server.call_tool("search_properties", {"project_name": f"Secret Unapproved Villa {rand_id}"})
    text_repr = str(search_res)
    assert f"Secret Unapproved Villa {rand_id}" not in text_repr, "Unpublished DRAFT project must not appear in public MCP search."

    # 3. Call public get_project_details
    details_res = await server.call_tool("get_project_details", {"project_name_or_id": f"prj_secret_{rand_id}"})
    assert "not an approved public listing" in str(details_res)


def test_developer_cannot_approve_own_project():
    """Verify that DEVELOPER_USER role is rejected with PermissionError when attempting publication approval."""
    with pytest.raises(PermissionError) as exc_info:
        approve_public(
            db=db,
            project_id="prj_secret_draft_99",
            actor_id="usr_dev_99",
            actor_role=InternalRole.DEVELOPER_USER,
        )
    assert "not authorized" in str(exc_info.value)


def test_auditor_cannot_resolve_legal_or_survey_flags():
    """Verify that AUDITOR role cannot resolve LAND_TITLE or HYDRAA risk flags."""
    flag_id = create_risk_flag(
        db=db,
        project_id="prj_secret_draft_99",
        category=VerificationCategory.LAND_TITLE,
        risk_type="POTENTIAL_22A_LISTING",
        severity="BLOCKING_HIGH",
        description="Survey number matches prohibited 22-A endowment land",
    )

    with pytest.raises(PermissionError) as exc_info:
        resolve_risk_flag(
            db=db,
            flag_id=flag_id,
            resolution_notes="Attempted auditor override",
            actor_id="usr_auditor_01",
            actor_role=InternalRole.AUDITOR,
        )
    assert "Only LEGAL_REVIEWER or ADMIN" in str(exc_info.value)


def test_blocking_high_flag_prevents_public_approval():
    """Verify that an unresolved BLOCKING_HIGH flag prevents even an ADMIN from approving."""
    with pytest.raises(ValueError) as exc_info:
        approve_public(
            db=db,
            project_id="prj_secret_draft_99",
            actor_id="usr_admin_01",
            actor_role=InternalRole.ADMIN,
        )
    assert "unresolved blocking risk flags" in str(exc_info.value)


def test_legal_reviewer_can_resolve_legal_flag():
    """Verify that LEGAL_REVIEWER can resolve land title flag with documented legal opinion."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM risk_flags WHERE project_id = 'prj_secret_draft_99' LIMIT 1")
        flag_id = cursor.fetchone()["id"]

    res = resolve_risk_flag(
        db=db,
        flag_id=flag_id,
        resolution_notes="Revenue department clearance certified under proc no 4402/2026",
        actor_id="usr_lawyer_01",
        actor_role=InternalRole.LEGAL_REVIEWER,
    )
    assert res["resolved"] is True


def test_suspended_project_immediately_delisted():
    """Verify that suspending an approved project removes it from public visibility."""
    # Suspend Sahith Home
    suspend_project(
        db=db,
        project_id="prj_sah_16751",
        reason="Routine legal re-verification audit",
        actor_id="usr_admin_01",
        actor_role=InternalRole.SUPER_ADMIN,
    )

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT project_status, public_visibility FROM projects WHERE id = 'prj_sah_16751'")
        p = cursor.fetchone()
        assert p["project_status"] == ProjectStatus.SUSPENDED
        assert p["public_visibility"] == 0

        # Verify not in public view
        cursor.execute("SELECT count(*) FROM public_project_views WHERE project_id = 'prj_sah_16751'")
        assert cursor.fetchone()[0] == 0

    # Re-instate for other tests
    approve_public(
        db=db,
        project_id="prj_sah_16751",
        actor_id="usr_admin_01",
        actor_role=InternalRole.SUPER_ADMIN,
    )


def test_public_verification_summary_omits_private_notes():
    """Verify that get_public_verification_summary returns verified dates and statuses but NO private notes."""
    summary = get_public_verification_summary(db=db, project_name_or_id="Sahith Home")
    assert summary["status"] == "success"
    assert "verification_categories" in summary
    assert "TG_RERA" in summary["verification_categories"]

    # Verify no internal private fields leaked
    serialized = str(summary)
    assert "extracted_text" not in serialized
    assert "file_bytes" not in serialized
    assert "reviewer_notes" not in serialized


@pytest.mark.anyio
async def test_submit_property_enquiry_isolated_write():
    """Verify that submit_property_enquiry writes only to user_inquiries and cannot modify project records."""
    res = await server.call_tool(
        "submit_property_enquiry",
        {
            "project_name_or_id": "Sahith Home",
            "buyer_name": "Rohan Patel",
            "buyer_contact": "rohan@testbuyer.com",
            "inquiry_message": "Need cost sheet for East-facing 5 BHK unit",
            "consent_given": True,
        },
    )
    assert "success" in str(res)

    # Verify inquiry recorded in user_inquiries
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT project_name, user_message FROM user_inquiries WHERE user_message LIKE '%East-facing%'"
        )
        inq = cursor.fetchone()
        assert inq is not None

        # Verify project record was NOT modified
        cursor.execute("SELECT name, developer FROM projects WHERE id = 'prj_sah_16751'")
        p = cursor.fetchone()
        assert p["name"] == "Sahith Home"
        assert p["developer"] == "Sahith"
