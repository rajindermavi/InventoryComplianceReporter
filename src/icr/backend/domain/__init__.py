"""Domain package.
- Identifying AMS-marked vessels (config-driven)
- Matching vessels between AMS index and inventory sources
- Matching inventory items onboard vessels to IC reference inventory
- Normalizing editions prior to comparison
- Classifying inventory discrepancies into issue rows
"""

from .compare import compare_inventory, normalize_edition
from .models import IssueRow, IssueType
from .queries import get_ams_vessels, get_onboard_inventory, get_reference_inventory

__all__ = [
    "IssueRow",
    "IssueType",
    "compare_inventory",
    "normalize_edition",
    "get_ams_vessels",
    "get_onboard_inventory",
    "get_reference_inventory",
]
