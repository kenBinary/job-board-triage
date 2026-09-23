from nicegui import ui

from src.indeed.db import GetIndeedDetailsFilters
from src.jobstreet.db import GetJobstreetDetailsFilters
from src.olj.db import GetOljDetailsFilters
from src.view.global_state import global_state
from src.view.indeed.indeed_state import indeed_state
from src.view.jobstreet.jobstreet_state import jobstreet_state
from src.view.olj.olj_state import olj_state


def filter_bar_view(on_filter_changed):
    def on_toggle_new(e):
        match global_state.job_board:
            case "Jobstreet":
                filters = GetJobstreetDetailsFilters(is_new=e.value)
                jobstreet_state.get_jobs(filters=filters)
            case "Indeed":
                filters = GetIndeedDetailsFilters(is_new=e.value)
                indeed_state.get_jobs(filters=filters)
            case "OLJ":
                filters = GetOljDetailsFilters(is_new=e.value)
                olj_state.get_jobs(filters=filters)

        on_filter_changed()

    with ui.card().classes(
        "w-full bg-white border border-slate-200/80 shadow-none rounded-md px-3 py-2"
    ):
        with ui.row().classes("w-full items-center justify-between gap-3"):
            with ui.row().classes("items-center gap-4 flex-1"):
                ui.checkbox(
                    "Show NEW only",
                    value=global_state.show_new_only,
                    on_change=on_toggle_new,
                ).props("dense").classes("text-sm font-medium text-slate-700")
