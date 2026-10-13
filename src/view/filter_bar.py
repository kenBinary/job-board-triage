from typing import get_args
from nicegui import ui

from src.indeed.db import GetIndeedDetailsFilters
from src.jobstreet.db import GetJobstreetDetailsFilters
from src.kalibrr.db import GetKalibrrDetailsFilters
from src.linkedin_posts.models.extraction_schemas import JobCategory
from src.mynimo.db import GetMynimoDetailsFilters
from src.olj.db import GetOljDetailsFilters
from src.view.global_state import global_state
from src.view.indeed.indeed_state import indeed_state
from src.view.jobstreet.jobstreet_state import jobstreet_state
from src.view.kalibrr.kalibrr_state import kalibrr_state
from src.view.linkedin.linkedin_state import linkedin_state
from src.view.facebook.facebook_state import facebook_state
from src.view.mynimo.mynimo_state import mynimo_state
from src.view.olj.olj_state import olj_state

LINKEDIN_CATEGORIES = ["All Categories"] + list(get_args(JobCategory))


@ui.refreshable
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
            case "Mynimo":
                filters = GetMynimoDetailsFilters(is_new=e.value)
                mynimo_state.get_jobs(filters=filters)
            case "Kalibrr":
                filters = GetKalibrrDetailsFilters(is_new=e.value)
                kalibrr_state.get_jobs(filters=filters)
            case "LinkedIn":
                linkedin_state.get_jobs(is_new=e.value)
            case "Facebook":
                facebook_state.get_jobs(is_new=e.value)
        global_state.show_new_only = e.value

        on_filter_changed()

    def on_category_changed(e):
        if global_state.job_board == "LinkedIn":
            linkedin_state.category = None if e.value == "All Categories" else e.value
            linkedin_state.get_jobs(
                category=linkedin_state.category,
                is_new=global_state.show_new_only,
                skip=0,
                limit=linkedin_state.paginated_jobs.page_size,
            )
        elif global_state.job_board == "Facebook":
            facebook_state.category = None if e.value == "All Categories" else e.value
            facebook_state.get_jobs(
                category=facebook_state.category,
                is_new=global_state.show_new_only,
                skip=0,
                limit=facebook_state.paginated_jobs.page_size,
            )
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

                if global_state.job_board == "LinkedIn":
                    current_category = linkedin_state.category or "All Categories"
                    ui.select(
                        options=LINKEDIN_CATEGORIES,
                        value=current_category,
                        on_change=on_category_changed,
                    ).props("dense outlined options-dense").classes("w-64 text-xs")

                if global_state.job_board == "Facebook":
                    current_category = facebook_state.category or "All Categories"
                    ui.select(
                        options=LINKEDIN_CATEGORIES,
                        value=current_category,
                        on_change=on_category_changed,
                    ).props("dense outlined options-dense").classes("w-64 text-xs")
