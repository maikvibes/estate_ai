from __future__ import annotations

import json
import logging
from typing import Any, Dict

from google.adk import Agent

from app.core.config import get_settings

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are a strict Listing Review Agent for real estate classifieds. Follow the WARNING.csv rules exactly.
Output ONLY structured JSON that matches the required schema; do not include prose.
Business rules (do not relax):
- Image Quality: flag blurry/low-res (<1080p) or missing required rooms (e.g., missing toilet/bathroom photo).
- Price Logic: flag if asking price is >40\\% \\below reasonable comps, or if comparison is invalid (e.g., new build vs 10-year-old mismatch). Use MANUAL_REVIEW if context is insufficient.
- Fraud/Risk: flag phrases like "deposit required before viewing", "advance fee", "scam", or similar risk signals.
- Feedback Quality: feedback MUST be actionable (specific reasons), never generic refusals.
False positives hurt users. If unsure, choose MANUAL_REVIEW with concrete questions.
Schema to return:
{
  "status": "APPROVED" | "REJECTED" | "MANUAL_REVIEW",
  "risk_score": integer 0-100,
  "feedback": ["specific, actionable bullet"]
}
"""


class ListingReviewer:
    """Runs a Google ADK Agent to review listings against business rules."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.agent = self._create_agent()

    def _create_agent(self) -> Any:
        return Agent(
            name="listing_reviewer",
            model=self.settings.google_genai_model,
            instructions=SYSTEM_PROMPT,
        )

    async def review(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        result = await self.agent.run(json.dumps(listing))

        try:
            parsed = json.loads(getattr(result, "text", "{}"))
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            logger.exception("Agent returned non-JSON payload")
            return {"status": "MANUAL_REVIEW", "risk_score": 50, "feedback": ["Could not parse agent response"]}
