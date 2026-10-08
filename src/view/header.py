from nicegui import ui

from src.indeed.db import GetIndeedDetailsFilters
from src.jobstreet.db import GetJobstreetDetailsFilters
from src.kalibrr.db import GetKalibrrDetailsFilters
from src.mynimo.db import GetMynimoDetailsFilters
from src.olj.db import GetOljDetailsFilters
from src.view.global_state import global_state
from src.view.indeed.indeed_state import indeed_state
from src.view.jobstreet.jobstreet_state import jobstreet_state
from src.view.kalibrr.kalibrr_state import kalibrr_state
from src.view.linkedin.linkedin_state import linkedin_state
from src.view.mynimo.mynimo_state import mynimo_state
from src.view.olj.olj_state import olj_state


@ui.refreshable
def header_view(on_job_board_change):
    with ui.row().classes("w-full items-center justify-between"):
        with ui.row().classes("items-center gap-2.5"):
            ui.label("Job Board Triage Engine").classes(
                "text-xl font-bold tracking-tight text-slate-900"
            )

        with ui.row().classes("items-center gap-2.5"):

            def handle_reset():
                # TODO: implement
                pass

            ui.button("Reset Data", on_click=handle_reset).props(
                "no-caps dense size=md"
            ).classes(
                "text-slate-700 hover:bg-slate-50 border-slate-300 font-medium px-3 rounded"
            )

            def handle_mark_all_as_seen():
                match global_state.job_board:
                    case "Jobstreet":
                        jobstreet_state.update_all_jobs_as_seen()
                    case "Indeed":
                        indeed_state.update_all_jobs_as_seen()
                    case "OLJ":
                        olj_state.update_all_jobs_as_seen()
                    case "Mynimo":
                        mynimo_state.update_all_jobs_as_seen()
                    case "Kalibrr":
                        kalibrr_state.update_all_jobs_as_seen()
                    case "LinkedIn":
                        linkedin_state.update_all_jobs_as_seen()
                on_job_board_change()

            ui.button("Mark all as seen", on_click=handle_mark_all_as_seen).props(
                "no-caps dense size=md"
            ).classes(
                "text-slate-700 hover:bg-slate-50 border-slate-300 font-medium px-3 rounded"
            )

    with ui.row().classes("w-full items-center justify-between"):
        with ui.row().classes("items-center gap-3"):

            def handle_job_board_change(e):
                if e.value == "Jobstreet":
                    filters = GetJobstreetDetailsFilters(
                        is_new=global_state.show_new_only
                    )
                    jobstreet_state.get_jobs(filters=filters)
                if e.value == "Indeed":
                    filters = GetIndeedDetailsFilters(is_new=global_state.show_new_only)
                    indeed_state.get_jobs(filters=filters)
                if e.value == "OLJ":
                    filters = GetOljDetailsFilters(is_new=global_state.show_new_only)
                    olj_state.get_jobs(filters=filters)
                if e.value == "Mynimo":
                    filters = GetMynimoDetailsFilters(is_new=global_state.show_new_only)
                    mynimo_state.get_jobs(filters=filters)
                if e.value == "Kalibrr":
                    filters = GetKalibrrDetailsFilters(
                        is_new=global_state.show_new_only
                    )
                    kalibrr_state.get_jobs(filters=filters)
                if e.value == "LinkedIn":
                    linkedin_state.get_jobs(is_new=global_state.show_new_only)
                on_job_board_change()

            ui.toggle(
                options=["Jobstreet", "Indeed", "OLJ", "Mynimo", "Kalibrr", "LinkedIn"],
                on_change=handle_job_board_change,
            ).bind_value(global_state, "job_board")
