"""Utility functions for CLI output."""

import click


def success(message: str) -> None:
    """Print success message in green."""
    click.echo(click.style(f"✓ {message}", fg="green"))


def error(message: str) -> None:
    """Print error message in red."""
    click.echo(click.style(f"✗ {message}", fg="red"), err=True)


def warning(message: str) -> None:
    """Print warning message in yellow."""
    click.echo(click.style(f"⚠ {message}", fg="yellow"))


def info(message: str) -> None:
    """Print info message in blue."""
    click.echo(click.style(f"ℹ {message}", fg="blue"))


def format_table(headers: list[str], rows: list[list[str]]) -> str:
    """Format data as a simple table.
    
    Args:
        headers: Column headers
        rows: List of row data
        
    Returns:
        Formatted table string
    """
    if not rows:
        return "No data"
    
    # Calculate column widths
    widths = [len(h) for h in headers]
    
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
    
    # Build separator
    separator = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    
    # Build header
    header_row = "|" + "|".join(f" {h:<{widths[i]}} " for i, h in enumerate(headers)) + "|"
    
    # Build data rows
    data_rows = []
    for row in rows:
        row_str = "|" + "|".join(
            f" {str(cell):<{widths[i]}} " for i, cell in enumerate(row)
        ) + "|"
        data_rows.append(row_str)
    
    # Combine
    lines = [separator, header_row, separator] + data_rows + [separator]
    
    return "\n".join(lines)
