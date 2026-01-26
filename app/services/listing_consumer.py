import asyncio
import json
import logging
from typing import Any, Callable

import httpx
from aiokafka import AIOKafkaConsumer

from app.agents.listing_reviewer import ListingReviewer
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ListingConsumer:
    """Consumes listing events, runs reviewer, posts webhook."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.consumer: AIOKafkaConsumer | None = None
        self._shutdown = asyncio.Event()
        self.reviewer = ListingReviewer()

    async def start(self) -> None:
        if self.consumer:
            return
        self.consumer = AIOKafkaConsumer(
            self.settings.kafka_listings_topic,
            bootstrap_servers=self.settings.kafka_bootstrap_servers,
            group_id=f"{self.settings.kafka_consumer_group}-listing",
            enable_auto_commit=True,
            auto_offset_reset="latest",
        )
        await self.consumer.start()
        logger.info("Listing consumer started")
        asyncio.create_task(self._consume_loop())

    async def stop(self) -> None:
        self._shutdown.set()
        if self.consumer:
            await self.consumer.stop()
        logger.info("Listing consumer stopped")

    async def _consume_loop(self) -> None:
        assert self.consumer
        try:
            while not self._shutdown.is_set():
                msg = await self.consumer.getone()
                asyncio.create_task(self._handle_message(msg.value))
        except asyncio.CancelledError:
            logger.info("Listing consumer loop cancelled")
        except Exception:
            logger.exception("Listing consumer loop crashed")

    async def _handle_message(self, raw: bytes) -> None:
        try:
            listing: dict[str, Any] = json.loads(raw)
        except json.JSONDecodeError:
            logger.exception("Invalid listing payload")
            return

        try:
            result = await self.reviewer.review(listing)
        except Exception:
            logger.exception("Reviewer failed, sending manual review fallback")
            result = {"status": "MANUAL_REVIEW", "risk_score": 50, "feedback": ["Reviewer error"]}

        await self._post_webhook(result)

    async def _post_webhook(self, payload: dict[str, Any]) -> None:
        headers = {"X-Secret-Key": self.settings.listing_review_secret}
        url = self.settings.listing_review_webhook_url
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
            except Exception:
                logger.exception("Webhook post failed")
