import asyncio
from typing import Optional
import typer

from src.cli.board_registry import get_boards_by_speed
from src.cli.orchestrator import RetryMode, ScraperOrchestrator
from src.common.enums.job_board import JobBoardEnum
from src.common.infra.camofoux_provider import PROFILE_DIR, CamofouxProvider
from src.common.infra.dependencies import infra_container
from src.common.logger import setup_logging

app = typer.Typer(add_completion=False)


def parse_target_boards(
    board: Optional[str], fast: bool, slow: bool
) -> list[JobBoardEnum]:
    if fast and slow:
        raise typer.BadParameter("Cannot specify both --fast and --slow.")
    if (fast or slow) and board:
        raise typer.BadParameter(
            "Cannot specify --board together with --fast or --slow."
        )

    if fast:
        return get_boards_by_speed(is_slow=False)
    if slow:
        return get_boards_by_speed(is_slow=True)
    if board:
        names = [b.strip().lower() for b in board.split(",") if b.strip()]
        valid_map = {b.value.lower(): b for b in JobBoardEnum}
        invalid = [name for name in names if name not in valid_map]

        if invalid:
            raise typer.BadParameter(
                f"Unknown board(s): {', '.join(invalid)}. Valid options: {', '.join(valid_map.keys())}"
            )
        return [valid_map[name] for name in names]

    return list(JobBoardEnum)


@app.command()
def main(
    board: Optional[str] = typer.Option(
        None,
        "--board",
        "-b",
        help="Comma-separated list of job boards (e.g. indeed,olj).",
    ),
    fast: bool = typer.Option(False, "--fast", help="Run only fast scrapers."),
    slow: bool = typer.Option(False, "--slow", help="Run only slow scrapers."),
    retry: bool = typer.Option(
        False, "--retry", "-r", help="Force resume without prompting."
    ),
    fresh: bool = typer.Option(
        False, "--fresh", help="Force fresh start without prompting."
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logs."),
    write_to_file: bool = typer.Option(
        False, "--write-to-file", "-wtf", help="Write logs to file."
    ),
    headless: bool = typer.Option(
        False, "--headless", help="Run browser in headless mode."
    ),
):
    """Run job board scrapers with custom board and state filters."""
    setup_logging(verbose=verbose, write_to_file=write_to_file)

    camoufox_provider = CamofouxProvider(
        headless=headless,
        persistent_context=True,
        user_data_dir=PROFILE_DIR,
        humanize=True,
        firefox_user_prefs={
            "widget.windows.window_occlusion_tracking.enabled": False,
            "dom.timeout.enable_budget_timer_throttling": False,
        },
    )
    infra_container.camoufox_provider = camoufox_provider

    if retry and fresh:
        raise typer.BadParameter(
            "Cannot specify both --retry and --fresh at the same time."
        )

    mode = (
        RetryMode.FORCE_RETRY
        if retry
        else (RetryMode.FORCE_FRESH if fresh else RetryMode.PROMPT)
    )
    targets = parse_target_boards(board, fast, slow)

    orchestrator = ScraperOrchestrator()
    asyncio.run(orchestrator.run(boards=targets, mode=mode))


if __name__ == "__main__":
    app()
