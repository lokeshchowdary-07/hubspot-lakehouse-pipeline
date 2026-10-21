"""
Pipeline configuration management using pydantic-settings.
Loads configuration from environment variables and/or .env file.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --------------------------------------------------------------------------
    # Mock HubSpot API Settings
    # --------------------------------------------------------------------------
    hubspot_api_base_url: str = Field(
        default="http://localhost:8080",
        description="Base URL for the HubSpot API (or Mock HubSpot service)",
    )
    hubspot_api_token: str = Field(
        default="mock-dev-token-secret-123",
        description="Static bearer token for API authentication",
    )
    hubspot_timeout_seconds: float = Field(
        default=30.0,
        description="HTTP request timeout in seconds",
    )

    # --------------------------------------------------------------------------
    # MinIO / S3 Lakehouse Storage Settings
    # --------------------------------------------------------------------------
    minio_endpoint_url: str = Field(
        default="http://localhost:9000",
        description="Endpoint URL for host access to MinIO",
    )
    minio_internal_endpoint_url: str = Field(
        default="http://minio:9000",
        description="Endpoint URL for container-to-container access (e.g. ClickHouse s3 function)",
    )
    minio_access_key: str = Field(
        default="minioadmin",
        description="MinIO root/access user",
    )
    minio_secret_key: str = Field(
        default="minioadmin",
        description="MinIO root/access secret key",
    )
    minio_bucket: str = Field(
        default="hubspot-lake",
        description="Target Lakehouse bucket name",
    )
    minio_region: str = Field(
        default="us-east-1",
        description="MinIO / S3 region identifier",
    )

    # --------------------------------------------------------------------------
    # ClickHouse Warehouse Settings
    # --------------------------------------------------------------------------
    clickhouse_host: str = Field(
        default="localhost",
        description="ClickHouse host address",
    )
    clickhouse_http_port: int = Field(
        default=8123,
        description="ClickHouse HTTP interface port",
    )
    clickhouse_native_port: int = Field(
        default=9100,
        description="ClickHouse native TCP client port (mapped from 9000 on host)",
    )
    clickhouse_user: str = Field(
        default="default",
        description="ClickHouse username",
    )
    clickhouse_password: str = Field(
        default="",
        description="ClickHouse password",
    )
    clickhouse_database: str = Field(
        default="hubspot",
        description="Target analytical database in ClickHouse",
    )

    # --------------------------------------------------------------------------
    # Pipeline Runner & Control Plane Settings
    # --------------------------------------------------------------------------
    control_db_path: Path = Field(
        default=Path("state/control.db"),
        description="SQLite control plane database path",
    )
    dlt_pipelines_dir: Path = Field(
        default=Path("state/dlt"),
        description="Directory where dlt persists local pipeline states",
    )
    pipeline_chunk_pages: int = Field(
        default=20,
        description="Number of API pages (typically 100 items each) per micro-batch commit chunk",
    )
    max_parallel_workers: int = Field(
        default=4,
        description="Max worker threads/processes for concurrent resource extraction",
    )
    heartbeat_timeout_seconds: float = Field(
        default=60.0,
        description="Heartbeat expiration duration before a worker is marked crashed",
    )

    # --------------------------------------------------------------------------
    # Derived Properties & Helpers
    # --------------------------------------------------------------------------
    @property
    def s3_bucket_url(self) -> str:
        """Returns the s3:// URL for the target bucket."""
        return f"s3://{self.minio_bucket}"

    @property
    def s3_credentials_dict(self) -> Dict[str, Any]:
        """Credentials dict compatible with dlt filesystem destination and s3fs."""
        return {
            "aws_access_key_id": self.minio_access_key,
            "aws_secret_access_key": self.minio_secret_key,
            "endpoint_url": self.minio_endpoint_url,
            "region_name": self.minio_region,
        }


@lru_cache()
def get_settings() -> Settings:
    """Returns a cached singleton Settings instance."""
    return Settings()
