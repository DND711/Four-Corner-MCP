"""
MCP Apps UI Resources and Templates for Four Corner.
"""

from pathlib import Path

UI_DIR = Path(__file__).parent

def get_property_card_html() -> str:
    """Return the raw HTML content for the property card UI resource."""
    html_path = UI_DIR / "property_card.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<div>Four Corner Property Card</div>"
