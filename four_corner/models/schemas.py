"""
Pydantic schemas and response models for Four Corner MCP Server.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RoomDimension(BaseModel):
    room_name: str = Field(description="Name of the room (e.g., Master Bedroom, Living Room)")
    dimensions_feet: str = Field(description="Dimensions in feet, e.g., '14'0\" x 12'6\"'")
    carpet_area_sqft: float = Field(description="Actual usable carpet area in square feet")
    natural_light_facing: str = Field(description="Window or balcony facing orientation, e.g., East, North-East")


class BalconyDetails(BaseModel):
    name: str = Field(description="Balcony label (e.g., Living Balcony, Master Bedroom Sitout)")
    dimensions_feet: str = Field(description="Dimensions in feet")
    orientation: str = Field(description="Orientation, e.g., East-Facing Corner")
    morning_sunlight: bool = Field(description="Whether the balcony captures direct morning sunlight")


class FloorPlanDetails(BaseModel):
    unit_id: str
    project_name: str
    developer: str
    bhk: float
    super_built_up_sqft: int
    carpet_area_sqft: int
    usable_efficiency_pct: float
    facing: str
    is_corner_unit: bool
    rooms: List[RoomDimension]
    balconies: List[BalconyDetails]
    vastu_compliance_summary: Dict[str, str]
    floor_plan_image_url: Optional[str] = Field(default=None, description="Architectural blueprint schematic image URL")
    interactive_3d_tour_url: Optional[str] = Field(default=None, description="Interactive 3D model walkthrough video URL")
    master_plan_url: Optional[str] = Field(default=None, description="Approved overall master layout plan URL")
    brochure_pdf_url: Optional[str] = Field(default=None, description="Official builder e-brochure PDF URL")


class PriceBreakdown(BaseModel):
    unit_id: str
    project_name: str
    developer: str
    super_built_up_sqft: int
    carpet_area_sqft: int
    base_rate_per_sqft_inr: int
    base_cost_inr: int
    floor_rise_charges_inr: int
    corner_premium_charges_inr: int
    clubhouse_charges_inr: int
    car_parking_slots: int
    car_parking_charges_inr: int
    infrastructure_and_water_inr: int
    gst_inr: int
    total_out_the_door_inr: int
    total_in_crores: float
    true_cost_per_carpet_sqft_inr: int
    broker_commission_inr: int = 0
    guarantee: str = "100% Direct Developer Pricing · Zero Broker Markup"


class CommuteEstimate(BaseModel):
    origin_project: str
    origin_micro_market: str
    destination_hub: str
    distance_km: float
    non_peak_mins: int
    rush_hour_morning_mins: int
    rush_hour_evening_mins: int
    primary_corridor: str
    key_intersections: List[str]
    congestion_warning: Optional[str] = None


class RERAVerification(BaseModel):
    rera_id: str
    project_name: str
    developer: str
    promoter_legal_entity: str
    sanctioning_authority: str
    approved_towers: int
    registered_handover_date: str
    status: str
    escrow_account_compliant: bool
    litigations_reported: int
    quarterly_compliance_up_to_date: bool
    rera_certificate_pdf_url: Optional[str] = Field(default=None, description="Direct download link to official TS-RERA certificate PDF")
    sanctioned_master_plan_pdf_url: Optional[str] = Field(default=None, description="Sanctioned building layout and master plan PDF")
    official_brochure_pdf_url: Optional[str] = Field(default=None, description="Verified builder sales brochure PDF")


class UnitSearchResult(BaseModel):
    unit_id: str
    project_name: str
    developer: str
    micro_market: str
    bhk: float
    facing: str
    is_corner_unit: bool
    carpet_area_sqft: int
    super_built_up_sqft: int
    usable_efficiency_pct: float
    total_price_cr: float
    handover_date: str
    rera_id: str
    hero_image_url: Optional[str] = Field(default=None, description="High-resolution exterior elevation image")
    floor_plan_image_url: Optional[str] = Field(default=None, description="Architectural 2D floor plan blueprint image")
    walkthrough_video_url: Optional[str] = Field(default=None, description="Direct 4K virtual walkthrough video URL")
    brochure_pdf_url: Optional[str] = Field(default=None, description="Official builder e-brochure PDF URL")


class ProjectMedia(BaseModel):
    project_id: str
    project_name: str
    developer: str
    micro_market: str
    rera_id: str
    hero_image_url: str
    gallery_images: List[str]
    walkthrough_video_url: str
    drone_footage_url: Optional[str] = None
    construction_update_video_url: Optional[str] = None
    brochure_pdf_url: str
    rera_certificate_url: str
    master_plan_url: str
    cost_sheet_pdf_url: Optional[str] = None
    site_progress_photos: List[str] = Field(default_factory=list)
