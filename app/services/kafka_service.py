import asyncio
import json
import logging
from typing import Any, Awaitable, Callable, Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from app.core.config import get_settings

logger = logging.getLogger(__name__)

MessageHandler = Callable[[dict[str, Any]], Awaitable[None]]


class KafkaService:
    """Async Kafka wrapper that manages producer/consumer lifecycle."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._producer: Optional[AIOKafkaProducer] = None
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._consume_task: Optional[asyncio.Task[None]] = None
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        await self._start_producer()
        await self._start_consumer()

    async def stop(self) -> None:
        self._shutdown_event.set()
        if self._consume_task:
            self._consume_task.cancel()
            try:
                await self._consume_task
            except asyncio.CancelledError:
                pass

        if self._consumer:
            await self._consumer.stop()
        if self._producer:
            await self._producer.stop()

    async def _start_producer(self) -> None:
        if self._producer:
            return
        self._producer = AIOKafkaProducer(bootstrap_servers=self.settings.kafka_bootstrap_servers)
        await self._producer.start()
        logger.info("Kafka producer started")

    async def _start_consumer(self) -> None:
        if self._consumer:
            return
        self._consumer = AIOKafkaConsumer(
            self.settings.kafka_requests_topic,
            bootstrap_servers=self.settings.kafka_bootstrap_servers,
            group_id=self.settings.kafka_consumer_group,
            enable_auto_commit=True,
            auto_offset_reset="latest",
        )
        await self._consumer.start()
        logger.info("Kafka consumer started")

    async def send(self, topic: str, payload: dict[str, Any]) -> None:
        if not self._producer:
            await self._start_producer()
        assert self._producer
        value = json.dumps(payload).encode("utf-8")
        await self._producer.send_and_wait(topic, value=value)

    async def consume_forever(self, handler: MessageHandler) -> None:
        """Spawn a non-blocking consumption loop.

        We create a task so FastAPI startup isn't blocked and so we can cancel gracefully.
        Each message is handled in its own task to isolate failures.
        """

        if not self._consumer:
            await self._start_consumer()
        assert self._consumer

        async def _loop() -> None:
            try:
                while not self._shutdown_event.is_set():
                    msg = await self._consumer.getone()
                    try:
                        data = json.loads(msg.value)
                        # Handle message in background to keep polling responsive.
                        asyncio.create_task(self._safe_handle(handler, data))
                    except json.JSONDecodeError:
                        logger.exception("Failed to decode Kafka message")
            except asyncio.CancelledError:
                logger.info("Kafka consumer loop cancelled")
            except Exception:
                logger.exception("Kafka consumer loop crashed")

        self._consume_task = asyncio.create_task(_loop())

    async def _safe_handle(self, handler: MessageHandler, data: dict[str, Any]) -> None:
        try:
            await handler(data)
        except Exception:
            # Guard so one bad message does not crash the consumer.
            logger.exception("Handler failed for message: %s", data)
