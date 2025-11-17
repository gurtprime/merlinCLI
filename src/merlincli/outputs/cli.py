"""CLI entrypoint for Merlin analysis."""

from __future__ import annotations

import json
from pathlib import Path

import click

from ..config import DEFAULT_CONFIG, PipelineConfig
from ..pipeline import MerlinPipeline


@click.group()
def cli() -> None:
    """Merlin CLI for BTC/USD analytics."""


@cli.command()
@click.option(
    "--timeframe",
    default=None,
    help="Candlestick timeframe, e.g. 1h, 4h, 15m (defaults to config value)"
)
@click.option("--limit", default=None, type=int, show_default=True, help="Max candles to fetch (defaults to config value)")
def analyze(timeframe: str | None, limit: int | None) -> None:
    """Run full BTC/USD analysis pipeline."""
    # Start with config that respects environment variables
    config = PipelineConfig().with_env_overrides()
    # CLI arguments override config and env vars
    if timeframe is not None:
        config.market.timeframe = timeframe
    if limit is not None:
        config.market.limit = limit
    pipeline = MerlinPipeline(config=config)
    result = pipeline.run()
    click.echo("=== MERLIN BTC/USD SNAPSHOT ===")
    click.echo(f"Symbol: {result['meta']['symbol']} on {result['meta']['exchange']}")
    click.echo(f"Timeframe: {result['meta']['timeframe']}  Last: {result['meta']['price']:.2f}")
    click.echo("--- Technicals ---")
    for key, value in result["technicals"].items():
        click.echo(f"{key}: {value}")
    click.echo("--- Sentiment ---")
    for key, value in result["sentiment"].items():
        click.echo(f"{key}: {value}")
    click.echo("--- Regime ---")
    for key, value in result["regime"].items():
        click.echo(f"{key}: {value}")
    click.echo("--- LLM Insight ---")
    click.echo(result["llm"]["rationale"])
    click.echo(f"Recommendation: {result['llm']['recommendation']}")
    click.echo("Risks: " + result["llm"].get("risks", "N/A"))
    if result["llm"].get("key_levels"):
        click.echo("Key levels: " + ", ".join(result["llm"]["key_levels"]))


@cli.command()
def dump() -> None:
    """Dump raw JSON payload for integrations."""
    pipeline = MerlinPipeline()
    result = pipeline.run()
    click.echo(json.dumps(result, indent=2, default=str))


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
