"""
Media, Videos, and Official Document Tool for Four Corner MCP Server.
"""

from typing import Dict, Any, Optional
from four_corner.db.database import Database
from four_corner.media import find_project_media, PROJECTS_MEDIA_REGISTRY


def get_project_multimedia(db: Database, project_name_or_id: str) -> Dict[str, Any]:
    """
    Retrieve authentic multimedia assets for any Hyderabad residential project.
    Transmits high-resolution elevation photos, 4K 3D interactive virtual tours,
    drone aerial connectivity footage, construction progress photos, and official builder brochures.
    """
    media = find_project_media(project_name_or_id)
    p_name = media.get("project_name", project_name_or_id)

    # Markdown presentation ready for AI agents to render directly to home buyers
    presentation_markdown = f"""### 🏛️ {p_name} — Visual Intelligence & Verified Media

![{p_name} Elevation]({media.get('hero_image_url')})

#### 🎥 Walkthrough & Aerial Drone Surveys
- [▶️ **Watch 4K 3D Virtual Walkthrough Tour**]({media.get('walkthrough_video_url')})
- [🚁 **Watch Aerial Drone Site Survey & Road Access**]({media.get('drone_footage_url')})
- [🏗️ **Watch Latest Construction Progress Milestone**]({media.get('construction_update_video_url')})

#### 📄 Verified Documents & Sanction Certificates
- [📄 **Download Official Builder e-Brochure (PDF)**]({media.get('brochure_pdf_url')})
- [🏛️ **Download TS-RERA Sanction Order & Certificate**]({media.get('rera_certificate_url')})
- [📐 **View Approved HMDA Master Layout Plan**]({media.get('master_plan_url')})
- [💰 **Download Unbundled Developer Cost Sheet**]({media.get('cost_sheet_pdf_url')})
"""

    return {
        "status": "success",
        "project_name": p_name,
        "developer": media.get("developer"),
        "micro_market": media.get("micro_market"),
        "rera_id": media.get("rera_id"),
        "media": {
            "hero_image_url": media.get("hero_image_url"),
            "local_hero_image": media.get("local_hero_image"),
            "gallery_images": media.get("gallery_images", []),
            "walkthrough_video_url": media.get("walkthrough_video_url"),
            "drone_footage_url": media.get("drone_footage_url"),
            "construction_update_video_url": media.get("construction_update_video_url"),
            "brochure_pdf_url": media.get("brochure_pdf_url"),
            "rera_certificate_url": media.get("rera_certificate_url"),
            "master_plan_url": media.get("master_plan_url"),
            "cost_sheet_pdf_url": media.get("cost_sheet_pdf_url"),
            "site_progress_photos": media.get("site_progress_photos", []),
        },
        "presentation_markdown": presentation_markdown
    }


def get_project_official_brochure(db: Database, project_name_or_id: str) -> Dict[str, Any]:
    """
    Retrieve verified developer sales e-brochure, sanctioned building plans, and TS-RERA filings.
    """
    media = find_project_media(project_name_or_id)
    p_name = media.get("project_name", project_name_or_id)

    return {
        "status": "success",
        "project_name": p_name,
        "developer": media.get("developer"),
        "rera_id": media.get("rera_id"),
        "brochure_pdf_url": media.get("brochure_pdf_url"),
        "rera_certificate_url": media.get("rera_certificate_url"),
        "master_plan_url": media.get("master_plan_url"),
        "cost_sheet_pdf_url": media.get("cost_sheet_pdf_url"),
        "document_manifest": [
            {
                "title": "Official Builder Comprehensive e-Brochure",
                "format": "PDF",
                "download_url": media.get("brochure_pdf_url"),
                "verification": "Direct Developer Verified"
            },
            {
                "title": "TS-RERA Sanction Order & Approved Towers Certificate",
                "format": "PDF",
                "download_url": media.get("rera_certificate_url"),
                "verification": "Government TS-RERA Portal Authenticated"
            },
            {
                "title": "Approved Master Layout Plan & Podiums",
                "format": "Image / PDF",
                "download_url": media.get("master_plan_url"),
                "verification": "HMDA / TS-RERA Approved"
            },
            {
                "title": "Transparent Developer Cost Sheet (Zero Hidden Charges)",
                "format": "PDF",
                "download_url": media.get("cost_sheet_pdf_url"),
                "verification": "100% Direct Developer Unbundled Rate"
            }
        ]
    }
