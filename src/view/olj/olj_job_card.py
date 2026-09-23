from nicegui import ui

from src.db.database import SessionLocal
from src.olj.db import update_olj_details
from src.olj.models.olj_job_details import OljJobDetails
from src.utils.date_utils import calculate_time_difference, format_date


def olj_job_card(job: OljJobDetails, on_refresh):
    def mark_seen():
        job.is_new = False
        with SessionLocal() as db:
            update_olj_details(db, job)

        on_refresh()

    with ui.card().classes(
        "w-full bg-white border border-slate-200/80 hover:border-slate-300 shadow-none rounded-md p-3 transition-colors"
    ):
        with ui.row().classes("w-full items-start justify-between no-wrap gap-3"):
            # Select Checkbox
            with ui.column().classes("pt-0.5"):
                ui.checkbox(
                    value=job.is_new,
                    on_change=lambda _: setattr(job, "is_new", True),
                ).props("dense")

            # Main Info
            with ui.column().classes("flex-1 gap-1 min-w-0"):
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    if job.is_new:
                        ui.label("NEW").classes(
                            "text-[10px] font-bold text-emerald-800 bg-emerald-100 border border-emerald-200 px-1.5 py-0.2 rounded"
                        )
                    ui.label(job.title).classes(
                        "text-sm font-bold text-slate-900 leading-tight"
                    )

                with ui.row().classes("items-center gap-2 flex-wrap"):
                    time_diff = calculate_time_difference(job.posted_at_utc)
                    ui.label(time_diff if time_diff else "Unknown").classes(
                        "text-sm text-amber-500 leading-tight"
                    )
                    formatted_posted_at = (
                        format_date(job.posted_at_utc)
                        if job.posted_at_utc
                        else "Unknown"
                    )
                    ui.label(f"{formatted_posted_at}").classes(
                        "text-sm text-green-600 leading-tight"
                    )

                # Company • Location • Type • Salary
                with ui.row().classes(
                    "items-center gap-1.5 text-xs text-slate-500 flex-wrap"
                ):
                    ui.label(
                        job.company_name if job.company_name else "Unknown"
                    ).classes("font-semibold text-slate-700")
                    ui.label("•")
                    ui.label(job.work_type if job.work_type else "Unknown")
                    ui.label("•")
                    ui.label(
                        job.formatted_salary if job.formatted_salary else "Unknown"
                    ).classes(
                        "font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200/60 px-1.5 py-0.2 rounded text-[11px]"
                    )

                with ui.row().classes(
                    "items-center gap-1.5 text-xs text-slate-500 flex-wrap"
                ):
                    for tag in job.tags or []:
                        ui.label(tag).classes(
                            "bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded-full text-xs font-medium border border-slate-200 shadow-sm"
                        )

            # Actions Column
            with ui.row().classes("items-end gap-1.5 shrink-0"):
                if job.is_new:
                    ui.button("Mark as Seen", on_click=mark_seen).props(
                        "outline no-caps dense size=md"
                    ).classes(
                        "text-slate-700 bg-white border-slate-300 hover:bg-slate-50 font-medium px-2.5 rounded"
                    )

                ui.link("Apply ↗", job.url if job.url else "#", new_tab=True).classes(
                    "bg-blue-600 h-full hover:bg-blue-700 text-white text-sm font-medium px-3 py-1 rounded no-underline inline-block text-center"
                )
