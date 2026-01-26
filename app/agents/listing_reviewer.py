from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List

from google import genai
from google.genai import types as genai_types

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
    """Runs a Google GenAI Agent to review listings against business rules."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = genai.Client(api_key=self.settings.google_genai_api_key)
        self.agent = self._create_agent()

    def _create_agent(self) -> Any:
        return self.client.agents.create(
            model=self.settings.google_genai_model,
            display_name="listing-reviewer",
            instruction=SYSTEM_PROMPT,
        )

    async def review(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        # The SDK is sync today; run in a thread to avoid blocking the event loop.
        return await asyncio.to_thread(self._run_sync, listing)

    def _run_sync(self, listing: Dict[str, Any]) -> Dict[str, Any]:
        # Prepare structured conversation: include listing JSON in a clear chunk.
        messages = [
            genai_types.Content(parts=[genai_types.Part.from_text(json.dumps(listing))])
        ]

        result = self.client.agents.chat(
            agent=self.agent.name,
            messages=messages,
            response_mime_type="application/json",
        )

        try:
            parsed = json.loads(getattr(result, "text", "{}"))
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            logger.exception("Agent returned non-JSON payload")
            return {"status": "MANUAL_REVIEW", "risk_score": 50, "feedback": ["Could not parse agent response"]}
