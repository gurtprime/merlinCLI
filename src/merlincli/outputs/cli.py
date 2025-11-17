"""CLI entrypoint for Merlin analysis."""

from __future__ import annotations

import json
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..config import DEFAULT_CONFIG, PipelineConfig
from ..pipeline import MerlinPipeline

console = Console()


@click.group()
def cli() -> None:
    """Merlin CLI for BTC/USD analytics."""


def _get_recommendation_color(recommendation: str) -> str:
    """Get color for recommendation."""
    rec = recommendation.upper()
    if rec == "LONG":
        return "green"
    elif rec == "SHORT":
        return "red"
    else:
        return "yellow"


def _format_value(value: float | int | str, key: str = "") -> str:
    """Format numeric values with appropriate precision."""
    if isinstance(value, (int, float)):
        if "ratio" in key.lower() or "position" in key.lower():
            return f"{value:.3f}"
        elif "score" in key.lower() or "bias" in key.lower() or "trend" in key.lower():
            return f"{value:.3f}"
        elif "volatility" in key.lower():
            return f"{value:.4f}"
        elif "price" in key.lower():
            return f"${value:,.2f}"
        else:
            return f"{value:.2f}"
    return str(value)


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
    
    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing market data...", total=None)
        pipeline = MerlinPipeline(config=config)
        result = pipeline.run()
        progress.update(task, completed=True)
    
    # Header
    price = result['meta']['price']
    symbol = result['meta']['symbol']
    exchange = result['meta']['exchange']
    tf = result['meta']['timeframe']
    
    header_text = Text()
    header_text.append("🔮 MERLIN ", style="bold magenta")
    header_text.append("BTC/USD", style="bold cyan")
    header_text.append(" Market Analysis", style="bold white")
    
    console.print()
    console.print(Panel(header_text, style="bold", border_style="magenta"))
    console.print()
    
    # Market Overview
    overview = Table.grid(padding=(0, 2))
    overview.add_column(style="cyan", justify="right")
    overview.add_column(style="white")
    overview.add_row("Symbol:", f"[bold]{symbol}[/bold]")
    overview.add_row("Exchange:", f"[bold]{exchange}[/bold]")
    overview.add_row("Timeframe:", f"[bold]{tf}[/bold]")
    overview.add_row("Price:", f"[bold green]${price:,.2f}[/bold green]")
    
    console.print(Panel(overview, title="📊 Market Overview", border_style="cyan"))
    console.print()
    
    # Technical Indicators
    tech_table = Table(show_header=True, header_style="bold yellow", border_style="yellow")
    tech_table.add_column("Indicator", style="cyan", width=20)
    tech_table.add_column("Value", style="white", justify="right")
    
    for key, value in result["technicals"].items():
        formatted_value = _format_value(value, key)
        # Color code some indicators
        if "rsi" in key.lower():
            if value > 70:
                formatted_value = f"[red]{formatted_value}[/red]"
            elif value < 30:
                formatted_value = f"[green]{formatted_value}[/green]"
        elif "trend" in key.lower():
            if value > 0:
                formatted_value = f"[green]{formatted_value}[/green]"
            else:
                formatted_value = f"[red]{formatted_value}[/red]"
        elif "bb_position" in key.lower():
            if value < 0.2:
                formatted_value = f"[red]{formatted_value}[/red] (Oversold)"
            elif value > 0.8:
                formatted_value = f"[green]{formatted_value}[/green] (Overbought)"
        
        tech_table.add_row(key.replace("_", " ").title(), formatted_value)
    
    console.print(Panel(tech_table, title="📈 Technical Indicators", border_style="yellow"))
    console.print()
    
    # Sentiment
    sent_table = Table(show_header=True, header_style="bold blue", border_style="blue")
    sent_table.add_column("Metric", style="cyan", width=20)
    sent_table.add_column("Value", style="white", justify="right")
    
    for key, value in result["sentiment"].items():
        formatted_value = _format_value(value, key)
        if "compound" in key.lower():
            if value > 0.05:
                formatted_value = f"[green]{formatted_value}[/green]"
            elif value < -0.05:
                formatted_value = f"[red]{formatted_value}[/red]"
        sent_table.add_row(key.replace("_", " ").title(), formatted_value)
    
    console.print(Panel(sent_table, title="💭 Sentiment Analysis", border_style="blue"))
    console.print()
    
    # Regime
    regime_table = Table(show_header=True, header_style="bold magenta", border_style="magenta")
    regime_table.add_column("Signal", style="cyan", width=20)
    regime_table.add_column("Value", style="white", justify="right")
    
    recommendation = result["regime"]["recommendation"]
    rec_color = _get_recommendation_color(recommendation)
    
    for key, value in result["regime"].items():
        if key == "recommendation":
            regime_table.add_row(
                key.replace("_", " ").title(),
                f"[bold {rec_color}]{recommendation}[/bold {rec_color}]"
            )
        else:
            formatted_value = _format_value(value, key)
            if "score" in key.lower() or "momentum" in key.lower():
                if value > 0:
                    formatted_value = f"[green]{formatted_value}[/green]"
                else:
                    formatted_value = f"[red]{formatted_value}[/red]"
            regime_table.add_row(key.replace("_", " ").title(), formatted_value)
    
    console.print(Panel(regime_table, title="🎯 Trading Regime", border_style="magenta"))
    console.print()
    
    # LLM Insight
    llm_rec = result["llm"]["recommendation"]
    llm_rec_color = _get_recommendation_color(llm_rec)
    
    rationale = result["llm"]["rationale"]
    risks = result["llm"].get("risks", "N/A")
    key_levels = result["llm"].get("key_levels", [])
    
    insight_content = Text()
    insight_content.append("Recommendation: ", style="bold")
    insight_content.append(f"{llm_rec}\n\n", style=f"bold {llm_rec_color}")
    insight_content.append("Rationale:\n", style="bold")
    insight_content.append(rationale, style="white")
    
    console.print(Panel(insight_content, title="🤖 LLM Insight", border_style="green"))
    console.print()
    
    # Risks
    if risks and risks != "N/A":
        risks_content = Text()
        for line in risks.split("\n"):
            if line.strip():
                risks_content.append("• ", style="yellow")
                risks_content.append(line.strip() + "\n", style="white")
        
        console.print(Panel(risks_content, title="⚠️  Risks", border_style="red"))
        console.print()
    
    # Key Levels
    if key_levels:
        levels_table = Table(show_header=True, header_style="bold cyan", border_style="cyan")
        levels_table.add_column("Type", style="cyan", width=15)
        levels_table.add_column("Level", style="white", justify="right")
        levels_table.add_column("Description", style="dim white")
        
        for level in key_levels:
            if isinstance(level, str):
                # Try to parse "Type: Value - Description" format
                if ":" in level:
                    parts = level.split(":", 1)
                    level_type = parts[0].strip()
                    rest = parts[1].strip()
                    if " - " in rest:
                        value, desc = rest.split(" - ", 1)
                        levels_table.add_row(level_type, value.strip(), desc.strip())
                    else:
                        levels_table.add_row(level_type, rest, "")
                else:
                    levels_table.add_row("Level", level, "")
            else:
                levels_table.add_row("Level", str(level), "")
        
        console.print(Panel(levels_table, title="📍 Key Levels", border_style="cyan"))
        console.print()


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
