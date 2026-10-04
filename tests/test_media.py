"""
Tests for Project Images, Videos, Floor Plans, and Official Brochures Transmission via MCP.
"""

import pytest
from starlette.testclient import TestClient
from four_corner.server import (
    search_properties,
    get_floor_plan,
    verify_rera,
    get_project_media,
    get_project_brochure,
    app,
)


def test_search_properties_transmits_media():
    """Verify that search_properties transmits hero images, floor plans, videos, and brochures."""
    res = search_properties(micro_market="Tellapur")
    assert res["status"] == "success"
    assert res["matched_count"] > 0
    
    first_prop = res["properties"][0]
    assert "hero_image_url" in first_prop and first_prop["hero_image_url"] is not None
    assert "floor_plan_image_url" in first_prop and first_prop["floor_plan_image_url"] is not None
    assert "walkthrough_video_url" in first_prop and first_prop["walkthrough_video_url"] is not None
    assert "brochure_pdf_url" in first_prop and first_prop["brochure_pdf_url"] is not None
    assert first_prop["hero_image_url"].startswith("http") or first_prop["hero_image_url"].startswith("/assets")


def test_get_floor_plan_transmits_media():
    """Verify that get_floor_plan transmits architectural blueprints and 3D walkthroughs."""
    res = get_floor_plan(unit_id="AKR-T3-1202")
    assert res["status"] == "success"
    plan = res["floor_plan"]
    
    assert plan["floor_plan_image_url"] is not None
    assert plan["interactive_3d_tour_url"] is not None
    assert plan["master_plan_url"] is not None
    assert plan["brochure_pdf_url"] is not None

    assert "media_assets" in res
    assert res["media_assets"]["floor_plan_blueprint"] is not None
    assert res["media_assets"]["model_walkthrough_video"] is not None


def test_verify_rera_transmits_documents():
    """Verify that verify_rera transmits official TS-RERA certificate and sanction files."""
    res = verify_rera(project_name_or_rera_id="P02400005128")
    assert res["status"] == "success"
    verification = res["rera_verification"]
    
    assert verification["rera_certificate_pdf_url"] is not None
    assert verification["sanctioned_master_plan_pdf_url"] is not None
    assert verification["official_brochure_pdf_url"] is not None
    assert "official_documents" in res


def test_get_project_media_all_projects():
    """Verify get_project_media tool for specific projects including Aparna Sarovar Zenith."""
    projects_to_test = [
        "Aparna Sarovar Zenith",
        "My Home Akrida",
        "Candeur Lakescape",
        "Aparna Zenon",
        "SAS Crown",
    ]
    for p_name in projects_to_test:
        res = get_project_media(p_name)
        assert res["status"] == "success"
        media = res["media"]
        assert media["hero_image_url"] is not None
        assert len(media["gallery_images"]) >= 3
        assert media["walkthrough_video_url"] is not None
        assert media["drone_footage_url"] is not None
        assert media["brochure_pdf_url"] is not None
        assert media["rera_certificate_url"] is not None
        assert media["master_plan_url"] is not None
        assert len(media["site_progress_photos"]) >= 1
        assert "presentation_markdown" in res
        assert p_name in res["presentation_markdown"]


def test_get_project_brochure_tool():
    """Verify get_project_brochure tool delivers downloadable builder and RERA PDFs."""
    res = get_project_brochure("Aparna Sarovar Zenith")
    assert res["status"] == "success"
    assert res["brochure_pdf_url"].endswith(".pdf")
    assert res["rera_certificate_url"].endswith(".pdf")
    assert len(res["document_manifest"]) >= 4
    for doc in res["document_manifest"]:
        assert doc["download_url"] is not None
        assert doc["format"] in ["PDF", "Image / PDF"]


def test_rest_media_api_endpoints():
    """Verify REST API routes /api/v1/properties/media and /api/v1/properties/brochure."""
    client = TestClient(app)
    
    # 1. Media API
    resp = client.get("/api/v1/properties/media/Aparna%20Sarovar%20Zenith")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["media"]["hero_image_url"] is not None

    # 2. Brochure API
    resp2 = client.get("/api/v1/properties/brochure/Candeur%20Lakescape")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "success"
    assert data2["brochure_pdf_url"] is not None

    # 3. Static assets check
    resp3 = client.get("/assets/tower_exterior.jpg")
    assert resp3.status_code == 200
    assert resp3.headers["content-type"].startswith("image/")


def test_sahith_home_media_and_interactive_tile():
    """Verify Sahith Home media retrieval and interactive media tile HTML with slider, zoom, and video."""
    res = get_project_media("Sahith Home")
    assert res["status"] == "success"
    assert res["project_name"] == "Sahith Home"
    media = res["media"]
    assert media["hero_image_url"] is not None
    assert len(media["gallery_images"]) >= 3
    assert media["walkthrough_video_url"] is not None
    assert media["drone_footage_url"] is not None
    assert media["brochure_pdf_url"] is not None
    assert media["master_plan_url"] is not None
    assert len(media["site_progress_photos"]) >= 1

    tile_html = res.get("media_tile_html", "")
    assert len(tile_html) > 500
    # Slide controls
    assert "fcNextSlide_" in tile_html
    assert "fcPrevSlide_" in tile_html
    assert "fcSelectSlide_" in tile_html
    # Zoom controls
    assert "fcOpenZoom_" in tile_html
    assert "fcZoomIn_" in tile_html
    assert "fcZoomOut_" in tile_html
    assert "fcZoomReset_" in tile_html
    # Video player
    assert "iframe" in tile_html
    assert "Walkthrough" in tile_html


def test_register_project_persists_media_and_floor_plans():
    """Verify that registering a project with media preserves all images, videos, and blueprints."""
    client = TestClient(app)
    payload = {
        "project_name": "Test Luxury Heights",
        "developer": "Prestige Group",
        "micro_market": "Kokapet",
        "rera_id": "P02400998877",
        "handover_year": 2027,
        "hero_image_url": "https://example.com/hero.jpg",
        "gallery_images": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
        "walkthrough_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "drone_footage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "brochure_pdf_url": "https://example.com/brochure.pdf",
        "master_plan_url": "https://example.com/master_plan.png",
        "cost_sheet_pdf_url": "https://example.com/cost_sheet.pdf",
        "site_progress_photos": ["https://example.com/site1.jpg"],
        "units": [
            {
                "bhk": 3.0,
                "facing": "East",
                "super_built_up_sqft": 2000,
                "carpet_area_sqft": 1500,
                "floor_plan_image_url": "https://example.com/unit_blueprint.jpg"
            }
        ]
    }
    reg_resp = client.post("/api/v1/projects/register", json=payload)
    assert reg_resp.status_code == 200
    project_id = reg_resp.json()["project_id"]

    # Verify via media endpoint
    media_resp = client.get(f"/api/v1/properties/media/{project_id}")
    assert media_resp.status_code == 200
    m_data = media_resp.json()
    assert m_data["media"]["hero_image_url"] == "https://example.com/hero.jpg"
    assert "https://example.com/img1.jpg" in m_data["media"]["gallery_images"]
    assert m_data["media"]["master_plan_url"] == "https://example.com/master_plan.png"

    # Verify unit floor plan
    detail_resp = client.get(f"/api/v1/projects/{project_id}")
    assert detail_resp.status_code == 200
    p_units = detail_resp.json()["project"]["units"]
    assert len(p_units) == 1
    assert p_units[0]["floor_plan_image_url"] == "https://example.com/unit_blueprint.jpg"

