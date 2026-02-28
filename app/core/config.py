from functools import lru_cache
from pydantic import MongoDsn, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Environment variable names use uppercase with underscores by default.
    """

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", case_sensitive=False)

    app_name: str = Field(default="estate-ai", description="Service name for logging/metrics")
    environment: str = Field(default="dev", description="Deployment environment label")

    # Mongo
    mongodb_uri: MongoDsn = Field(default="mongodb://localhost:27017", description="Mongo connection string")
    mongodb_db: str = Field(default="estate_ai", description="Mongo database name")

    # Kafka
    kafka_bootstrap_servers: str = Field(default="localhost:9092", description="Comma-separated Kafka brokers")
    kafka_requests_topic: str = Field(default="agent.requests", description="Topic for inbound agent tasks")
    kafka_results_topic: str = Field(default="agent.results", description="Topic for processed outputs")
    kafka_consumer_group: str = Field(default="agent-workers", description="Consumer group for workers")
    kafka_listings_topic: str = Field(default="listings.new", description="Topic for new listing reviews")

    # Google GenAI / ADK
    google_genai_api_key: str = Field(default="", description="API key for Google Gen AI")
    google_genai_model: str = Field(default="models/gemini-1.5-pro", description="Model to run")

    # Vector store (Chroma local, no auth required)
    chroma_persist_dir: str = Field(default=".chroma", description="Directory for Chroma persistence")

    # Webhook
    listing_review_webhook_url: str = Field(
        default="https://api.estate.maik.io.vn/listings/review",
        description="Webhook endpoint for listing review results",
    )
    listing_review_secret: str = Field(default="", description="Shared secret for webhook auth header X-Secret-Key")

    # Server
    api_host: str = Field(default="0.0.0.0", description="FastAPI host binding")
    api_port: int = Field(default=8000, description="FastAPI port")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached instance of settings to avoid reparsing env."""

    return Settings()
