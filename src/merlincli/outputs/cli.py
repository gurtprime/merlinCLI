"""CLI entrypoint for Merlin analysis."""

from __future__ import annotations

import json
import re
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout

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


def _parse_key_levels(key_levels: list) -> tuple[list[dict], float, float]:
    """Parse key levels and extract price values."""
    levels = []
    prices = []
    
    for level in key_levels:
        if isinstance(level, str):
            # Parse "Type: Value - Description" or "Type: Value" or "Type: Value Description"
            if ":" in level:
                parts = level.split(":", 1)
                level_type = parts[0].strip().lower()
                rest = parts[1].strip()
                
                # Extract price value - try multiple patterns
                value_str = None
                desc = ""
                
                # Pattern 1: "Value - Description"
                if " - " in rest:
                    value_str = rest.split(" - ")[0].strip()
                    desc = rest.split(" - ", 1)[1].strip()
                # Pattern 2: "Value Description" (number followed by text)
                else:
                    # Find first number in the string
                    numbers = re.findall(r'\d+\.?\d*', rest)
                    if numbers:
                        value_str = numbers[0]
                        # Description is everything after the number
                        num_pos = rest.find(value_str)
                        if num_pos >= 0:
                            desc = rest[num_pos + len(value_str):].strip()
                
                if value_str:
                    try:
                        # Remove $ and commas, convert to float
                        value_clean = value_str.replace("$", "").replace(",", "").strip()
                        price = float(value_clean)
                        prices.append(price)
                        levels.append({
                            "type": level_type,
                            "price": price,
                            "description": desc
                        })
                    except (ValueError, IndexError):
                        continue
            else:
                # Try to extract number from string
                numbers = re.findall(r'\d+\.?\d*', level)
                if numbers:
                    try:
                        price = float(numbers[0])
                        prices.append(price)
                        levels.append({
                            "type": "level",
                            "price": price,
                            "description": level
                        })
                    except ValueError:
                        pass
    
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0
    
    return levels, min_price, max_price


def _create_price_chart(
    current_price: float,
    key_levels: list,
    recommendation: str,
    height: int = 20
) -> Text:
    """Create a visual price chart showing levels and expected movement."""
    levels, min_price, max_price = _parse_key_levels(key_levels)
    
    if not levels:
        return Text("No price levels available for chart", style="dim")
    
    # Add current price to range if needed
    all_prices = [current_price] + [l["price"] for l in levels]
    min_price = min(all_prices)
    max_price = max(all_prices)
    
    # Add some padding
    price_range = max_price - min_price
    if price_range == 0:
        price_range = current_price * 0.1  # 10% padding if no range
    padding = price_range * 0.1
    min_price -= padding
    max_price += padding
    price_range = max_price - min_price
    
    # Create chart
    chart_lines = []
    
    # Determine arrow direction based on recommendation
    if recommendation.upper() == "LONG":
        arrow = "↑"
        arrow_style = "green"
        direction = "UP"
    elif recommendation.upper() == "SHORT":
        arrow = "↓"
        arrow_style = "red"
        direction = "DOWN"
    else:
        arrow = "→"
        arrow_style = "yellow"
        direction = "SIDEWAYS"
    
    # Sort levels by price
    sorted_levels = sorted(levels, key=lambda x: x["price"], reverse=True)
    
    # Create vertical chart
    chart_height = height
    price_step = price_range / (chart_height - 1)
    
    # Create a mapping of price to chart line index
    price_to_line = {}
    for i in range(chart_height):
        price_at_line = min_price + (price_range * (i / (chart_height - 1)))
        price_to_line[price_at_line] = chart_height - 1 - i
    
    # Find closest line for each level and current price
    level_lines = {}
    for level in sorted_levels:
        level_price = level["price"]
        closest_line = min(range(chart_height), 
                          key=lambda i: abs((min_price + price_range * (i / (chart_height - 1))) - level_price))
        level_lines[closest_line] = level
    
    current_line = min(range(chart_height),
                      key=lambda i: abs((min_price + price_range * (i / (chart_height - 1))) - current_price))
    
    for i in range(chart_height):
        line_idx = chart_height - 1 - i
        price_at_line = min_price + (price_range * (i / (chart_height - 1)))
        
        line = Text()
        
        level_at_line = level_lines.get(line_idx)
        is_current = (line_idx == current_line)
        
        # Left side: price labels
        if level_at_line:
            level_type = level_at_line["type"].upper()
            if "resistance" in level_type or "res" in level_type:
                line.append(f"${level_at_line['price']:,.0f} ", style="bold red")
                line.append("▶", style="red")
            elif "support" in level_type or "sup" in level_type:
                line.append(f"${level_at_line['price']:,.0f} ", style="bold green")
                line.append("▶", style="green")
            else:
                line.append(f"${level_at_line['price']:,.0f} ", style="bold yellow")
                line.append("▶", style="yellow")
        elif is_current:
            line.append(f"${current_price:,.0f} ", style="bold cyan")
            line.append("●", style="bold cyan")
        else:
            line.append(" " * 12)
        
        # Middle: chart area with visual representation
        if level_at_line:
            level_type = level_at_line["type"].upper()
            if "resistance" in level_type or "res" in level_type:
                line.append("═" * 35, style="red")
            elif "support" in level_type or "sup" in level_type:
                line.append("═" * 35, style="green")
            else:
                line.append("═" * 35, style="yellow")
        elif is_current:
            line.append("─" * 35, style="bold cyan")
        else:
            # Show relative position with dots
            line.append("·" * 35, style="dim white")
        
        # Right side: labels
        if level_at_line:
            level_type = level_at_line["type"]
            line.append(f" {level_type.upper()}", style="dim")
        elif is_current:
            line.append(f" {arrow} CURRENT ({direction})", style=f"bold {arrow_style}")
        
        chart_lines.append(line)
    
    # Add summary at bottom
    summary = Text()
    summary.append("\nPrice Range: ", style="bold")
    summary.append(f"${min_price:,.0f}", style="green")
    summary.append(" → ", style="dim")
    summary.append(f"${max_price:,.0f}", style="red")
    summary.append(f" | Current: ", style="bold")
    summary.append(f"${current_price:,.0f}", style="bold cyan")
    summary.append(f" | Expected: ", style="bold")
    summary.append(direction, style=f"bold {arrow_style}")
    
    chart_text = Text()
    for line in chart_lines:
        chart_text.append(line)
        chart_text.append("\n")
    chart_text.append(summary)
    
    return chart_text


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
    
    # Price Chart with Key Levels
    if key_levels:
        chart = _create_price_chart(price, key_levels, llm_rec, height=18)
        console.print(Panel(chart, title="📊 Price Chart & Key Levels", border_style="cyan"))
        console.print()
    
    # Key Levels Table
    if key_levels:
        levels_table = Table(show_header=True, header_style="bold cyan", border_style="cyan")
        levels_table.add_column("Type", style="cyan", width=15)
        levels_table.add_column("Level", style="white", justify="right")
        levels_table.add_column("Description", style="dim white", width=60)
        
        for level in key_levels:
            level_type = "Level"
            level_value = ""
            description = ""
            
            if isinstance(level, dict):
                # Handle dict format from LLM
                level_type = level.get("type", "level")
                level_value = str(level.get("value") or level.get("level", ""))
                description = level.get("description", "")
            elif isinstance(level, str):
                # Parse string format "Type: Value - Description" or "Type: Value"
                if ":" in level:
                    parts = level.split(":", 1)
                    level_type = parts[0].strip()
                    rest = parts[1].strip()
                    
                    # Try multiple patterns
                    if " - " in rest:
                        value, desc = rest.split(" - ", 1)
                        level_value = value.strip()
                        description = desc.strip()
                    else:
                        # Try to extract number and description
                        numbers = re.findall(r'\d+\.?\d*', rest)
                        if numbers:
                            level_value = numbers[0]
                            # Description is everything after the number
                            num_pos = rest.find(level_value)
                            if num_pos >= 0:
                                desc_part = rest[num_pos + len(level_value):].strip()
                                if desc_part:
                                    description = desc_part
                        else:
                            level_value = rest
                else:
                    # Try to extract number from plain string
                    numbers = re.findall(r'\d+\.?\d*', level)
                    if numbers:
                        level_value = numbers[0]
                        description = level
                    else:
                        level_value = level
            
            # Format the value nicely
            try:
                value_float = float(str(level_value).replace("$", "").replace(",", ""))
                formatted_value = f"${value_float:,.2f}"
            except (ValueError, AttributeError):
                formatted_value = str(level_value) if level_value else "N/A"
            
            levels_table.add_row(
                level_type.title(),
                formatted_value,
                description if description else "[dim]No description[/dim]"
            )
        
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
