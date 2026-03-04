from __future__ import annotations

import logging
import asyncio
from typing import Any, Dict

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ListingReviewer:
    """Runs structural pattern matching to review listings against business rules."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def review(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        # Introduce a delay to simulate processing
        await asyncio.sleep(2.0)
        
        description = str(listing.get("description", "")).lower()
        price = listing.get("price", 0)
        
        # Use Python structural pattern matching
        match (description, price):
            case (desc, _) if any(keyword in desc for keyword in ["deposit required before viewing", "advance fee", "scam"]):
                return {
                    "status": "REJECTED", 
                    "risk_score": 90, 
                    "feedback": ["Fraud/Risk keywords found"]
                }
            case (_, p) if isinstance(p, (int, float)) and p < 100:
                return {
                    "status": "MANUAL_REVIEW", 
                    "risk_score": 50, 
                    "feedback": ["Price seems extremely low"]
                }
            case (desc, _) if "blurry" in desc or "missing" in desc:
                return {
                    "status": "MANUAL_REVIEW", 
                    "risk_score": 30, 
                    "feedback": ["Image quality or missing rooms mentioned in description"]
                }
            case _:
                return {
                    "status": "APPROVED", 
                    "risk_score": 10, 
                    "feedback": ["Listing complies with basic rules"]
                }
