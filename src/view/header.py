from nicegui import ui

from src.jobstreet.db import GetJobstreetDetailsFilters
from src.view.global_state import global_state
from src.view.jobstreet.jobstreet_state import jobstreet_state


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
                on_job_board_change()

            ui.toggle(
                options=["Jobstreet", "Indeed"], on_change=handle_job_board_change
            ).bind_value(global_state, "job_board")
