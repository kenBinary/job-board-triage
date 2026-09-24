from nicegui import ui

from src.indeed.db import GetIndeedDetailsFilters
from src.jobstreet.db import GetJobstreetDetailsFilters
from src.kalibrr.db import GetKalibrrDetailsFilters
from src.mynimo.db import GetMynimoDetailsFilters
from src.olj.db import GetOljDetailsFilters
from src.view.global_state import global_state
from src.view.indeed.indeed_job_card import indeed_job_card
from src.view.indeed.indeed_state import indeed_state
from src.view.jobstreet.jobstreet_job_card import jobsreet_job_card
from src.view.jobstreet.jobstreet_state import jobstreet_state
from src.view.kalibrr.kalibrr_job_card import kalibrr_job_card
from src.view.kalibrr.kalibrr_state import kalibrr_state
from src.view.mynimo.mynimo_job_card import mynimo_job_card
from src.view.mynimo.mynimo_state import mynimo_state
from src.view.olj.olj_job_card import olj_job_card
from src.view.olj.olj_state import olj_state


def render_pagination_bar(
    on_page_change,
    current_page: int,
    page_size: int,
    total_count: int,
    total_pages: int,
):
    actual_showing_from = (current_page - 1) * page_size + 1
    actual_showing_of = min(current_page * page_size, total_count)

    def handle_page_change(page: int):
        match global_state.job_board:
            case "Jobstreet":
                filters = GetJobstreetDetailsFilters(is_new=global_state.show_new_only)
                page = max(1, min(page, total_pages))
                jobstreet_state.get_jobs(
                    filters=filters, skip=(page - 1) * page_size, limit=page_size
                )
            case "Indeed":
                filters = GetIndeedDetailsFilters(is_new=global_state.show_new_only)
                page = max(1, min(page, total_pages))
                indeed_state.get_jobs(
                    filters=filters, skip=(page - 1) * page_size, limit=page_size
                )
            case "OLJ":
                filters = GetOljDetailsFilters(is_new=global_state.show_new_only)
                page = max(1, min(page, total_pages))
                olj_state.get_jobs(
                    filters=filters, skip=(page - 1) * page_size, limit=page_size
                )
            case "Mynimo":
                filters = GetMynimoDetailsFilters(is_new=global_state.show_new_only)
                page = max(1, min(page, total_pages))
                mynimo_state.get_jobs(
                    filters=filters, skip=(page - 1) * page_size, limit=page_size
                )
            case "Kalibrr":
                filters = GetKalibrrDetailsFilters(is_new=global_state.show_new_only)
                page = max(1, min(page, total_pages))
                kalibrr_state.get_jobs(
                    filters=filters, skip=(page - 1) * page_size, limit=page_size
                )
        on_page_change()

    def handle_page_size_change(size: int):
        on_page_change()
        match global_state.job_board:
            case "Jobstreet":
                filters = GetJobstreetDetailsFilters(is_new=global_state.show_new_only)
                jobstreet_state.get_jobs(filters=filters, skip=0, limit=size)
            case "Indeed":
                filters = GetIndeedDetailsFilters(is_new=global_state.show_new_only)
                indeed_state.get_jobs(filters=filters, skip=0, limit=size)
            case "OLJ":
                filters = GetOljDetailsFilters(is_new=global_state.show_new_only)
                olj_state.get_jobs(filters=filters, skip=0, limit=size)
            case "Mynimo":
                filters = GetMynimoDetailsFilters(is_new=global_state.show_new_only)
                mynimo_state.get_jobs(filters=filters, skip=0, limit=size)
            case "Kalibrr":
                filters = GetKalibrrDetailsFilters(is_new=global_state.show_new_only)
                kalibrr_state.get_jobs(filters=filters, skip=0, limit=size)
        on_page_change()

    def handle_goto_page(page: int):
        """Handler for the 'Go to' direct page input."""
        handle_page_change(page)

    with ui.row().classes(
        "w-full items-center justify-between px-4 py-3 bg-white border border-slate-200/80 rounded-md text-sm text-slate-500 shadow-none"
    ):
        with ui.row().classes("items-center gap-4"):
            ui.html(
                f'Showing <b class="text-slate-800 font-bold">{actual_showing_from}</b> '
                f'to <b class="text-slate-800 font-bold">{actual_showing_of}</b> '
                f'of <b class="text-slate-800 font-bold">{total_count}</b> jobs'
            )

            with ui.row().classes("items-center gap-2"):
                ui.label("Show:").classes("text-slate-500 text-sm")
                ui.select(
                    options=[10, 25, 50, 100],
                    value=page_size,
                    on_change=lambda e: handle_page_size_change(e.value),
                ).props("dense outlined options-dense").classes("w-20 text-xs").style(
                    "min-width: 68px;"
                )

        with ui.row().classes("items-center gap-1.5"):
            ui.button(
                "«",
                on_click=lambda: handle_page_change(0),
            ).props("flat dense no-caps").classes(
                "w-8 h-8 min-w-0 p-0 text-slate-400 hover:text-slate-600 border border-slate-200 rounded"
            )

            ui.button(
                "‹",
                on_click=lambda: handle_page_change(current_page - 1),
            ).props("flat dense no-caps").classes(
                "w-8 h-8 min-w-0 p-0 text-slate-400 hover:text-slate-600 border border-slate-200 rounded"
            )

            pages_to_show = []
            if total_pages <= 5:
                pages_to_show = list(range(1, total_pages + 1))
            else:
                if current_page <= 2:
                    pages_to_show = [1, 2, "...", total_pages]
                elif current_page >= total_pages - 1:
                    pages_to_show = [1, "...", total_pages - 1, total_pages]
                else:
                    pages_to_show = [1, "...", current_page, "...", total_pages]

            for item in pages_to_show:
                if item == "...":
                    ui.label("...").classes("px-1 text-slate-400 font-bold")
                else:
                    is_active = item == current_page
                    btn_classes = "w-8 h-8 min-w-0 p-0 rounded font-medium text-xs " + (
                        "bg-[#1976d2] text-white border border-[#1976d2]"
                        if is_active
                        else "bg-white text-slate-700 hover:bg-slate-50 border border-slate-200"
                    )
                    ui.button(
                        str(item),
                    ).props(
                        "flat dense no-caps"
                    ).classes(btn_classes)

            ui.button(
                "›",
                on_click=lambda: handle_page_change(current_page + 1),
            ).props("flat dense no-caps").classes(
                "w-8 h-8 min-w-0 p-0 text-slate-400 hover:text-slate-600 border border-slate-200 rounded"
            )

            ui.button(
                "»",
                on_click=lambda: handle_page_change(total_pages),
            ).props("flat dense no-caps").classes(
                "w-8 h-8 min-w-0 p-0 text-slate-400 hover:text-slate-600 border border-slate-200 rounded"
            )

            with ui.row().classes("items-center gap-1.5 ml-2"):
                ui.label("Go to:").classes("text-slate-500 text-sm")
                ui.number(
                    value=current_page,
                    min=1,
                    max=total_pages,
                    on_change=lambda e: handle_goto_page(int(e.value or 1)),
                ).props("dense outlined").classes("w-14 text-xs").style(
                    "min-width: 56px;"
                )


@ui.refreshable
def job_list_view(on_status_change, on_page_change):
    jobCount = 0
    match global_state.job_board:
        case "Jobstreet":
            jobCount = jobstreet_state.total_count
        case "Indeed":
            jobCount = indeed_state.total_count
        case "OLJ":
            jobCount = olj_state.total_count
        case "Mynimo":
            jobCount = mynimo_state.total_count
        case "Kalibrr":
            jobCount = kalibrr_state.total_count

    if jobCount == 0:
        with ui.card().classes(
            "w-full p-8 text-center bg-white border border-slate-200/80 rounded-md"
        ):
            ui.label("No jobs match your filter.").classes("text-slate-400 text-sm")
        return

    with ui.column().classes("w-full gap-2.5"):
        match global_state.job_board:
            case "Jobstreet":
                for job in jobstreet_state.jobs:
                    jobsreet_job_card(job, on_refresh=on_status_change)
                render_pagination_bar(
                    on_page_change=on_page_change,
                    current_page=jobstreet_state.paginated_jobs.page,
                    page_size=jobstreet_state.paginated_jobs.page_size,
                    total_count=jobstreet_state.paginated_jobs.total,
                    total_pages=jobstreet_state.paginated_jobs.total_pages,
                )
            case "Indeed":
                for job in indeed_state.jobs:
                    indeed_job_card(job, on_refresh=on_status_change)
                render_pagination_bar(
                    on_page_change=on_page_change,
                    current_page=indeed_state.paginated_jobs.page,
                    page_size=indeed_state.paginated_jobs.page_size,
                    total_count=indeed_state.paginated_jobs.total,
                    total_pages=indeed_state.paginated_jobs.total_pages,
                )
            case "OLJ":
                for job in olj_state.jobs:
                    olj_job_card(job, on_refresh=on_status_change)
                render_pagination_bar(
                    on_page_change=on_page_change,
                    current_page=olj_state.paginated_jobs.page,
                    page_size=olj_state.paginated_jobs.page_size,
                    total_count=olj_state.paginated_jobs.total,
                    total_pages=olj_state.paginated_jobs.total_pages,
                )
            case "Mynimo":
                for job in mynimo_state.jobs:
                    mynimo_job_card(job, on_refresh=on_status_change)
                render_pagination_bar(
                    on_page_change=on_page_change,
                    current_page=mynimo_state.paginated_jobs.page,
                    page_size=mynimo_state.paginated_jobs.page_size,
                    total_count=mynimo_state.paginated_jobs.total,
                    total_pages=mynimo_state.paginated_jobs.total_pages,
                )
            case "Kalibrr":
                for job in kalibrr_state.jobs:
                    kalibrr_job_card(job, on_refresh=on_status_change)
                render_pagination_bar(
                    on_page_change=on_page_change,
                    current_page=kalibrr_state.paginated_jobs.page,
                    page_size=kalibrr_state.paginated_jobs.page_size,
                    total_count=kalibrr_state.paginated_jobs.total,
                    total_pages=kalibrr_state.paginated_jobs.total_pages,
                )
