"""
Unit tests for Phase 0: Scaffold, configuration, and dlt API verification.
"""

from pathlib import Path
import pytest
from typer.testing import CliRunner

from hubspot_pipeline.config import Settings, get_settings
from hubspot_pipeline.cli import app


def test_settings_default_values():
    """Verify Settings initializes with expected defaults."""
    settings = Settings()
    assert settings.hubspot_api_base_url == "http://localhost:8080"
    assert settings.minio_bucket == "hubspot-lake"
    assert settings.clickhouse_http_port == 8123
    assert settings.clickhouse_native_port == 9100
    assert settings.s3_bucket_url == "s3://hubspot-lake"
    assert "aws_access_key_id" in settings.s3_credentials_dict
    assert settings.pipeline_chunk_pages == 20
    assert settings.max_parallel_workers == 4


def test_settings_singleton():
    """Verify get_settings returns consistent cached settings."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2


def test_cli_config_command():
    """Verify CLI config command runs without errors."""
    runner = CliRunner()
    result = runner.invoke(app, ["config"])
    assert result.exit_code == 0
    assert "hubspot_api_base_url" in result.stdout
    assert "s3_bucket_url" in result.stdout


def test_dlt_filesystem_and_incremental_contracts(tmp_path: Path):
    """
    Verify dlt API contracts for filesystem destination and incremental cursor.
    Asserts Parquet file creation and state cursor progression.
    """
    import dlt
    from dlt.destinations import filesystem
    from dlt.sources import incremental

    dest = filesystem(bucket_url=tmp_path.as_posix())

    @dlt.resource(primary_key="id")
    def sample_data(
        updated_at=incremental("updated_at", initial_value="1970-01-01T00:00:00.000Z", row_order="asc")
    ):
        yield [
            {"id": "c1", "name": "Alice", "updated_at": "2026-03-01T12:00:00.000Z"},
            {"id": "c2", "name": "Bob", "updated_at": "2026-03-01T12:00:00.000Z"},  # tie
            {"id": "c3", "name": "Charlie", "updated_at": "2026-03-01T13:00:00.000Z"},
        ]

    pipeline = dlt.pipeline(
        pipeline_name="p0_pipe",
        dataset_name="p0_data",
        pipelines_dir=str(tmp_path / "dlt"),
        destination=dest,
        dev_mode=True,
    )
    load_info = pipeline.run(sample_data(), loader_file_format="parquet")
    assert len(load_info.loads_ids) > 0

    # Verify Parquet files were created
    parquet_files = list(tmp_path.rglob("*.parquet"))
    assert len(parquet_files) >= 1

    # Verify incremental cursor state was updated to the latest timestamp
    resource_state = None
    for source in pipeline.state.get("sources", {}).values():
        if "sample_data" in source.get("resources", {}):
            resource_state = source["resources"]["sample_data"]["incremental"]["updated_at"]
            break

    assert resource_state is not None
    assert resource_state["last_value"] == "2026-03-01T13:00:00.000Z"
    assert "unique_hashes" in resource_state
