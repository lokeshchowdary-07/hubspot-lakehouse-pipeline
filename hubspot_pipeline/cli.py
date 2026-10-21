"""
Command-line interface for the HubSpot Lakehouse Pipeline using Typer and Rich.
Every Makefile target corresponds to a CLI command here.
"""

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="hubspot-pipeline",
    help="Fault-tolerant, incremental HubSpot ingestion pipeline using dlt, Parquet, MinIO, and ClickHouse.",
    add_completion=False,
)
console = Console()


@app.command()
def config() -> None:
    """Display the active pipeline configuration loaded from environment or .env file."""
    from hubspot_pipeline.config import get_settings

    settings = get_settings()
    table = Table(title="Pipeline Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="green")
    table.add_column("Value", style="yellow")

    for field_name, value in settings.model_dump().items():
        table.add_row(field_name, str(value))

    table.add_row("s3_bucket_url (derived)", settings.s3_bucket_url)
    console.print(table)


@app.command()
def status() -> None:
    """Display current control plane status, resource checkpoints, and runner state."""
    console.print("[yellow]Control plane status command initialized (Phase 6 implementation).[/yellow]")


@app.command()
def run(
    resources: str = typer.Option(None, "--resources", "-r", help="Comma-separated list of resources to ingest"),
    workers: int = typer.Option(4, "--workers", "-w", help="Number of parallel worker processes/threads"),
) -> None:
    """Execute the pipeline ingestion loop across CRM resources."""
    console.print(f"[yellow]Pipeline run command initialized with workers={workers} (Phase 6 implementation).[/yellow]")


@app.command()
def pause(
    resource: str = typer.Option(None, "--resource", help="Specific resource to pause, or all if omitted"),
) -> None:
    """Signal pipeline runners to pause gracefully at the next page/chunk checkpoint."""
    console.print(f"[yellow]Pause command initialized for resource={resource} (Phase 6 implementation).[/yellow]")


@app.command()
def resume() -> None:
    """Resume paused or interrupted pipeline runners from their last durable checkpoints."""
    console.print("[yellow]Resume command initialized (Phase 6 implementation).[/yellow]")


@app.command()
def load() -> None:
    """Load newly landed Parquet files from MinIO into ClickHouse ReplacingMergeTree tables."""
    console.print("[yellow]ClickHouse load command initialized (Phase 5 implementation).[/yellow]")


@app.command()
def verify() -> None:
    """Run mathematical checksum and deduplication verification between source and warehouse."""
    console.print("[yellow]Verification command initialized (Phase 7 implementation).[/yellow]")


@app.command()
def reset() -> None:
    """Reset all local control state, dlt pipelines, and temporary storage."""
    console.print("[yellow]Reset command initialized (Phase 6 implementation).[/yellow]")


@app.command()
def seed(
    profile: str = typer.Option("small", "--profile", "-p", help="Seed profile: 'small' (30k rows) or 'large' (1M+ rows)"),
) -> None:
    """Seed the mock HubSpot API with deterministic synthetic data."""
    console.print(f"[yellow]Seed command initialized with profile={profile} (Phase 2 implementation).[/yellow]")


@app.command()
def faults(
    rate_limit: float = typer.Option(0.0, "--rate-limit", help="Probability of 429 rate limit responses"),
    server_error: float = typer.Option(0.0, "--server-error", help="Probability of 500/503 responses"),
    latency_ms: int = typer.Option(0, "--latency-ms", help="Simulated network latency in milliseconds"),
) -> None:
    """Inject artificial faults and latency into the mock HubSpot API."""
    console.print(f"[yellow]Faults command initialized (rate_limit={rate_limit}, server_error={server_error}, latency={latency_ms}ms) (Phase 2 implementation).[/yellow]")


@app.command()
def demo() -> None:
    """Run an interactive narrated walkthrough of the pipeline resilience features."""
    console.print("[yellow]Interactive demo command initialized (Phase 9 implementation).[/yellow]")


if __name__ == "__main__":
    app()
