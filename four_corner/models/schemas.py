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
