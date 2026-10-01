"""
Configuration settings for Four Corner MCP Server.
"""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "db"
DATA_DIR = Path.home() / ".four-corner"
DEFAULT_DB_PATH = DATA_DIR / "four_corner.db"

# Server info
SERVER_NAME = "four-corner"
SERVER_VERSION = "0.1.0"

# Target Micro-Markets
SUPPORTED_MICRO_MARKETS = [
    "Kokapet",
    "Financial District",
    "Tellapur",
    "Narsingi",
    "Gachibowli",
    "Nanakramguda",
    "Kollur",
]

# Major IT & Commercial Destination Hubs for Commute Calculations
DESTINATION_HUBS = {
    "Financial District": {"lat": 17.4156, "lon": 78.3444, "label": "Financial District (Waverock / One West)"},
    "HITEC City": {"lat": 17.4474, "lon": 78.3762, "label": "HITEC City / Cyber Towers"},
    "Kokapet SEZ": {"lat": 17.3942, "lon": 78.3245, "label": "Kokapet Neopolis / SEZ"},
    "Gachibowli Junction": {"lat": 17.4401, "lon": 78.3489, "label": "Gachibowli Bio-Diversity / DLF"},
    "RGIA Airport": {"lat": 17.2403, "lon": 78.4294, "label": "Rajiv Gandhi International Airport (Shamshabad)"},
}
