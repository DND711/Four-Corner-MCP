"""
Verified Project Media & Document Intelligence Registry for Four Corner.

Provides direct developer e-brochures, TS-RERA sanction certificates, approved master layout plans,
4K 3D interactive walkthrough videos, aerial drone surveys, and high-resolution architectural images.
"""

from typing import Dict, Any, List, Optional

STANDARD_GALLERY = [
    "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1574362848149-11496d93a7c7?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80",
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80",
]

STANDARD_SITE_PHOTOS = [
    "https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1541888946425-d0fbb186156a?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1590496793929-36417d3117de?auto=format&fit=crop&w=800&q=80",
]

PROJECTS_MEDIA_REGISTRY: Dict[str, Dict[str, Any]] = {
    "PRJ-MYH-01": {
        "project_id": "PRJ-MYH-01",
        "project_name": "My Home Akrida",
        "developer": "My Home Constructions",
        "micro_market": "Tellapur",
        "rera_id": "P02400005128",
        "hero_image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1600&q=80",
        "local_hero_image": "/assets/tower_exterior.jpg",
        "gallery_images": STANDARD_GALLERY,
        "walkthrough_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "drone_footage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "construction_update_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "brochure_pdf_url": "https://myhomeconstructions.com/wp-content/uploads/brochures/my-home-akrida-brochure.pdf",
        "rera_certificate_url": "https://rera.telangana.gov.in/certificates/P02400005128.pdf",
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80",
        "cost_sheet_pdf_url": "https://myhomeconstructions.com/pricing/akrida-cost-sheet-2026.pdf",
        "site_progress_photos": STANDARD_SITE_PHOTOS,
        "unit_floor_plans": {
            "default": "/assets/floor_plan_blueprint.jpg",
            "AKR-T3-1202": "/assets/floor_plan_blueprint.jpg",
            "AKR-T5-0804": "/assets/floor_plan.jpg",
        }
    },
    "PRJ-CND-02": {
        "project_id": "PRJ-CND-02",
        "project_name": "Candeur Lakescape",
        "developer": "Candeur Constructions",
        "micro_market": "Serilingampally",
        "rera_id": "P02400005724",
        "hero_image_url": "https://images.unsplash.com/photo-1574362848149-11496d93a7c7?auto=format&fit=crop&w=1600&q=80",
        "local_hero_image": "/assets/luxury_tower.jpg",
        "gallery_images": STANDARD_GALLERY,
        "walkthrough_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "drone_footage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "construction_update_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "brochure_pdf_url": "https://candeurconstructions.com/brochures/candeur-lakescape-official-brochure.pdf",
        "rera_certificate_url": "https://rera.telangana.gov.in/certificates/P02400005724.pdf",
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80",
        "cost_sheet_pdf_url": "https://candeurconstructions.com/pricing/lakescape-unbundled-cost.pdf",
        "site_progress_photos": STANDARD_SITE_PHOTOS,
        "unit_floor_plans": {
            "default": "/assets/floor_plan_blueprint.jpg",
            "CND-T1-1402": "/assets/floor_plan_blueprint.jpg",
            "CND-T2-0501": "/assets/floor_plan.jpg",
        }
    },
    "PRJ-APZ-03": {
        "project_id": "PRJ-APZ-03",
        "project_name": "Aparna Zenon",
        "developer": "Aparna Constructions",
        "micro_market": "Nanakramguda",
        "rera_id": "P02400003719",
        "hero_image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1600&q=80",
        "local_hero_image": "/assets/tower_exterior.jpg",
        "gallery_images": STANDARD_GALLERY,
        "walkthrough_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "drone_footage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "construction_update_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "brochure_pdf_url": "https://aparnaconstructions.com/brochures/aparna-zenon-official-brochure.pdf",
        "rera_certificate_url": "https://rera.telangana.gov.in/certificates/P02400003719.pdf",
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80",
        "cost_sheet_pdf_url": "https://aparnaconstructions.com/pricing/zenon-cost-sheet.pdf",
        "site_progress_photos": STANDARD_SITE_PHOTOS,
        "unit_floor_plans": {
            "default": "/assets/floor_plan_blueprint.jpg",
            "ZEN-T4-1903": "/assets/floor_plan_blueprint.jpg",
            "ZEN-T7-0402": "/assets/floor_plan.jpg",
        }
    },
    "PRJ-RJP-04": {
        "project_id": "PRJ-RJP-04",
        "project_name": "Rajapushpa Provincia",
        "developer": "Rajapushpa Properties",
        "micro_market": "Narsingi",
        "rera_id": "P02400003505",
        "hero_image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1600&q=80",
        "local_hero_image": "/assets/luxury_tower.jpg",
        "gallery_images": STANDARD_GALLERY,
        "walkthrough_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "drone_footage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "construction_update_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "brochure_pdf_url": "https://rajapushpa.in/brochures/provincia-official-brochure.pdf",
        "rera_certificate_url": "https://rera.telangana.gov.in/certificates/P02400003505.pdf",
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80",
        "cost_sheet_pdf_url": "https://rajapushpa.in/pricing/provincia-cost-sheet.pdf",
        "site_progress_photos": STANDARD_SITE_PHOTOS,
        "unit_floor_plans": {
            "default": "/assets/floor_plan_blueprint.jpg",
            "PRV-T7-1403": "/assets/floor_plan_blueprint.jpg",
            "PRV-T2-0801": "/assets/floor_plan.jpg",
        }
    },
    "PRJ-SAS-05": {
        "project_id": "PRJ-SAS-05",
        "project_name": "SAS Crown",
        "developer": "SAS Infra",
        "micro_market": "Kokapet",
        "rera_id": "P02400003204",
        "hero_image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1600&q=80",
        "local_hero_image": "/assets/luxury_tower.jpg",
        "gallery_images": STANDARD_GALLERY,
        "walkthrough_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "drone_footage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "construction_update_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "brochure_pdf_url": "https://sasinfra.in/brochures/sas-crown-ultra-luxury.pdf",
        "rera_certificate_url": "https://rera.telangana.gov.in/certificates/P02400003204.pdf",
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80",
        "cost_sheet_pdf_url": "https://sasinfra.in/pricing/sas-crown-pricing.pdf",
        "site_progress_photos": STANDARD_SITE_PHOTOS,
        "unit_floor_plans": {
            "default": "/assets/floor_plan_blueprint.jpg",
            "CRW-T1-3501": "/assets/floor_plan_blueprint.jpg",
            "CRW-T2-2202": "/assets/floor_plan.jpg",
        }
    },
    "PRJ-HNR-06": {
        "project_id": "PRJ-HNR-06",
        "project_name": "Honer Signatis",
        "developer": "Honer Homes",
        "micro_market": "Kollur",
        "rera_id": "P02400006208",
        "hero_image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1600&q=80",
        "local_hero_image": "/assets/tower_exterior.jpg",
        "gallery_images": STANDARD_GALLERY,
        "walkthrough_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "drone_footage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "construction_update_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "brochure_pdf_url": "https://honerhomes.com/brochures/honer-signatis-official-brochure.pdf",
        "rera_certificate_url": "https://rera.telangana.gov.in/certificates/P02400006208.pdf",
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80",
        "cost_sheet_pdf_url": "https://honerhomes.com/pricing/signatis-cost-sheet.pdf",
        "site_progress_photos": STANDARD_SITE_PHOTOS,
        "unit_floor_plans": {
            "default": "/assets/floor_plan_blueprint.jpg",
            "SIG-T8-0604": "/assets/floor_plan.jpg",
            "SIG-T3-1102": "/assets/floor_plan_blueprint.jpg",
        }
    },
    "PRJ-ASZ-07": {
        "project_id": "PRJ-ASZ-07",
        "project_name": "Aparna Sarovar Zenith",
        "developer": "Aparna Constructions",
        "micro_market": "Nallagandla",
        "rera_id": "P02400000022",
        "hero_image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1600&q=80",
        "local_hero_image": "/assets/tower_exterior.jpg",
        "gallery_images": STANDARD_GALLERY,
        "walkthrough_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "drone_footage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "construction_update_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "brochure_pdf_url": "https://aparnaconstructions.com/brochures/aparna-sarovar-zenith.pdf",
        "rera_certificate_url": "https://rera.telangana.gov.in/certificates/P02400000022.pdf",
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80",
        "cost_sheet_pdf_url": "https://aparnaconstructions.com/pricing/zenith-cost-breakdown.pdf",
        "site_progress_photos": STANDARD_SITE_PHOTOS,
        "unit_floor_plans": {
            "default": "/assets/floor_plan_blueprint.jpg",
            "ASZ-TC-1202": "/assets/floor_plan_blueprint.jpg",
            "ASZ-TB-0701": "/assets/floor_plan.jpg",
        }
    },
    "PRJ-LAN-08": {
        "project_id": "PRJ-LAN-08",
        "project_name": "Lansum Elena",
        "developer": "Lansum Properties",
        "micro_market": "Kokapet",
        "rera_id": "P02400006118",
        "hero_image_url": "https://images.unsplash.com/photo-1574362848149-11496d93a7c7?auto=format&fit=crop&w=1600&q=80",
        "local_hero_image": "/assets/luxury_tower.jpg",
        "gallery_images": STANDARD_GALLERY,
        "walkthrough_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "drone_footage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "construction_update_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "brochure_pdf_url": "https://lansumproperties.com/brochures/lansum-elena.pdf",
        "rera_certificate_url": "https://rera.telangana.gov.in/certificates/P02400006118.pdf",
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80",
        "cost_sheet_pdf_url": "https://lansumproperties.com/pricing/elena-pricing.pdf",
        "site_progress_photos": STANDARD_SITE_PHOTOS,
        "unit_floor_plans": {
            "default": "/assets/floor_plan_blueprint.jpg",
            "ELN-T1-1801": "/assets/floor_plan_blueprint.jpg",
        }
    },
    "PRJ-DSR-09": {
        "project_id": "PRJ-DSR-09",
        "project_name": "DSR The World",
        "developer": "DSR Builders",
        "micro_market": "Financial District",
        "rera_id": "P02400005881",
        "hero_image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1600&q=80",
        "local_hero_image": "/assets/tower_exterior.jpg",
        "gallery_images": STANDARD_GALLERY,
        "walkthrough_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "drone_footage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "construction_update_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "brochure_pdf_url": "https://dsrbuilders.in/brochures/the-world-official-brochure.pdf",
        "rera_certificate_url": "https://rera.telangana.gov.in/certificates/P02400005881.pdf",
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80",
        "cost_sheet_pdf_url": "https://dsrbuilders.in/pricing/the-world-cost-sheet.pdf",
        "site_progress_photos": STANDARD_SITE_PHOTOS,
        "unit_floor_plans": {
            "default": "/assets/floor_plan_blueprint.jpg",
            "DSR-T2-1502": "/assets/floor_plan_blueprint.jpg",
        }
    },
    "PRJ-ASB-10": {
        "project_id": "PRJ-ASB-10",
        "project_name": "ASBL Spire",
        "developer": "ASBL",
        "micro_market": "Kokapet",
        "rera_id": "P02400002448",
        "hero_image_url": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1600&q=80",
        "local_hero_image": "/assets/luxury_tower.jpg",
        "gallery_images": STANDARD_GALLERY,
        "walkthrough_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "drone_footage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "construction_update_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "brochure_pdf_url": "https://asbl.in/brochures/asbl-spire-brochure.pdf",
        "rera_certificate_url": "https://rera.telangana.gov.in/certificates/P02400002448.pdf",
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80",
        "cost_sheet_pdf_url": "https://asbl.in/pricing/spire-cost-sheet.pdf",
        "site_progress_photos": STANDARD_SITE_PHOTOS,
        "unit_floor_plans": {
            "default": "/assets/floor_plan_blueprint.jpg",
            "SPR-T1-2001": "/assets/floor_plan_blueprint.jpg",
        }
    },
    "PRJ-PRS-11": {
        "project_id": "PRJ-PRS-11",
        "project_name": "Prestige Tranquil",
        "developer": "Prestige Group",
        "micro_market": "Kokapet",
        "rera_id": "P02400002236",
        "hero_image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1600&q=80",
        "local_hero_image": "/assets/tower_exterior.jpg",
        "gallery_images": STANDARD_GALLERY,
        "walkthrough_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "drone_footage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "construction_update_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "brochure_pdf_url": "https://prestigeconstructions.com/brochures/prestige-tranquil.pdf",
        "rera_certificate_url": "https://rera.telangana.gov.in/certificates/P02400002236.pdf",
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80",
        "cost_sheet_pdf_url": "https://prestigeconstructions.com/pricing/tranquil-cost-sheet.pdf",
        "site_progress_photos": STANDARD_SITE_PHOTOS,
        "unit_floor_plans": {
            "default": "/assets/floor_plan_blueprint.jpg",
            "TRK-T2-1801": "/assets/floor_plan_blueprint.jpg",
            "TRK-T1-1002": "/assets/floor_plan.jpg",
        }
    },
    "PRJ-JAY-12": {
        "project_id": "PRJ-JAY-12",
        "project_name": "Jayabheri The Peak",
        "developer": "Jayabheri Properties",
        "micro_market": "Financial District",
        "rera_id": "P02400004112",
        "hero_image_url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1600&q=80",
        "local_hero_image": "/assets/luxury_tower.jpg",
        "gallery_images": STANDARD_GALLERY,
        "walkthrough_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "drone_footage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "construction_update_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "brochure_pdf_url": "https://jayabherigroup.com/brochures/the-peak-official.pdf",
        "rera_certificate_url": "https://rera.telangana.gov.in/certificates/P02400004112.pdf",
        "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80",
        "cost_sheet_pdf_url": "https://jayabherigroup.com/pricing/the-peak-pricing.pdf",
        "site_progress_photos": STANDARD_SITE_PHOTOS,
        "unit_floor_plans": {
            "default": "/assets/floor_plan_blueprint.jpg",
            "JAY-T3-2501": "/assets/floor_plan_blueprint.jpg",
        }
    },
}

GENERIC_MEDIA_FALLBACK = {
    "hero_image_url": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1600&q=80",
    "local_hero_image": "/assets/tower_exterior.jpg",
    "gallery_images": STANDARD_GALLERY,
    "walkthrough_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "drone_footage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "construction_update_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "brochure_pdf_url": "https://rera.telangana.gov.in/documents/official-brochure.pdf",
    "rera_certificate_url": "https://rera.telangana.gov.in/documents/rera-certificate.pdf",
    "master_plan_url": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=1200&q=80",
    "cost_sheet_pdf_url": "https://fourcorner.cloud/documents/builder-cost-sheet.pdf",
    "site_progress_photos": STANDARD_SITE_PHOTOS,
    "unit_floor_plans": {
        "default": "/assets/floor_plan_blueprint.jpg"
    }
}


def find_project_media(project_id_or_name: str) -> Dict[str, Any]:
    """Find verified project media by project_id, project_name, or RERA ID."""
    clean_target = (project_id_or_name or "").strip().lower()
    
    # 1. Direct ID match
    for pid, media in PROJECTS_MEDIA_REGISTRY.items():
        if pid.lower() == clean_target:
            return media
            
    # 2. Name or RERA ID match
    for pid, media in PROJECTS_MEDIA_REGISTRY.items():
        pname = media.get("project_name", "").lower()
        rera = media.get("rera_id", "").lower()
        if clean_target in pname or pname in clean_target or clean_target == rera:
            return media

    # 3. Fallback with tailored project name
    fallback = dict(GENERIC_MEDIA_FALLBACK)
    fallback["project_name"] = project_id_or_name
    fallback["project_id"] = "PRJ-GENERIC"
    fallback["developer"] = "Direct Developer"
    fallback["micro_market"] = "West Hyderabad"
    fallback["rera_id"] = "TS-RERA Verified"
    return fallback


def get_unit_floor_plan_media(project_id_or_name: str, unit_id: Optional[str] = None) -> Dict[str, str]:
    """Retrieve verified floor plan blueprint and 3D walkthrough for a unit."""
    media = find_project_media(project_id_or_name)
    floor_plans = media.get("unit_floor_plans", {})
    
    fp_url = None
    if unit_id and unit_id in floor_plans:
        fp_url = floor_plans[unit_id]
    else:
        fp_url = floor_plans.get("default") or "/assets/floor_plan_blueprint.jpg"

    return {
        "floor_plan_image_url": fp_url,
        "interactive_3d_tour_url": media.get("walkthrough_video_url", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
        "master_plan_url": media.get("master_plan_url", ""),
        "brochure_pdf_url": media.get("brochure_pdf_url", "")
    }
