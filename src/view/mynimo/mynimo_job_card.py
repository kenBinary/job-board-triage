from nicegui import ui

from src.db.database import SessionLocal
from src.mynimo.db import update_mynimo_details
from src.mynimo.models.mynimo_job_details import MynimoJobDetails
from src.utils.date_utils import calculate_time_difference, format_date


def mynimo_job_card(job: MynimoJobDetails, on_refresh):
    def mark_seen():
        job.is_new = False
        with SessionLocal() as db:
            update_mynimo_details(db, job)
        on_refresh()

    job_url = job.url or f"https://www.mynimo.com/job/{job.job_id}"

    with ui.card().classes(
        "w-full bg-white border border-slate-200/80 hover:border-slate-300 shadow-none rounded-md p-3 transition-colors"
    ):
        with ui.row().classes("w-full items-start justify-between no-wrap gap-3"):
            with ui.column().classes("pt-0.5"):
                ui.checkbox(
                    value=job.is_new,
                    on_change=lambda _: setattr(job, "is_new", True),
                ).props("dense")

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

                with ui.row().classes(
                    "items-center gap-1.5 text-xs text-slate-500 flex-wrap"
                ):
                    ui.label(
                        job.company_name if job.company_name else "Unknown"
                    ).classes("font-semibold text-slate-700")
                    ui.label("•")
                    ui.label(job.location if job.location else "Unknown")
                    ui.label("•")
                    ui.label(job.work_type if job.work_type else "Full-time")

                    if not job.hide_salary and (job.salary_min or job.salary_max):
                        ui.label("•")
                        if job.salary_min and job.salary_max:
                            salary_display = f"PHP {job.salary_min:,.0f} - {job.salary_max:,.0f} / {job.salary_period or 'Monthly'}"
                        elif job.salary_min:
                            salary_display = f"PHP {job.salary_min:,.0f}+ / {job.salary_period or 'Monthly'}"
                        else:
                            salary_display = f"PHP up to {job.salary_max:,.0f} / {job.salary_period or 'Monthly'}"
                        ui.label(salary_display).classes(
                            "font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200/60 px-1.5 py-0.2 rounded text-[11px]"
                        )

                with ui.row().classes(
                    "items-center gap-1.5 text-xs text-slate-500 flex-wrap"
                ):
                    if job.is_urgent:
                        ui.label("Urgent").classes(
                            "font-semibold text-amber-700 bg-amber-50 border border-amber-200/60 px-1.5 py-0.2 rounded text-[11px]"
                        )
                    if job.work_from_home:
                        ui.label("Work from Home").classes(
                            "font-semibold text-blue-700 bg-blue-50 border border-blue-200/60 px-1.5 py-0.2 rounded text-[11px]"
                        )
                    if job.job_level:
                        ui.label(job.job_level).classes(
                            "bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded-full text-xs font-medium border border-slate-200 shadow-sm"
                        )
                    if job.company_size:
                        ui.label(job.company_size).classes(
                            "bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded-full text-xs font-medium border border-slate-200 shadow-sm"
                        )
                    if job.num_vacancies:
                        ui.label(f"{job.num_vacancies} vacancies").classes(
                            "bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded-full text-xs font-medium border border-slate-200 shadow-sm"
                        )
                    if job.high_school:
                        ui.label("High School").classes(
                            "bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded-full text-xs font-medium border border-slate-200 shadow-sm"
                        )
                    if job.is_pwd:
                        ui.label("PWD Friendly").classes(
                            "bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded-full text-xs font-medium border border-slate-200 shadow-sm"
                        )
                    if job.is_senior_citizen:
                        ui.label("Senior Citizen").classes(
                            "bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded-full text-xs font-medium border border-slate-200 shadow-sm"
                        )

            with ui.row().classes("items-end gap-1.5 shrink-0"):
                if job.is_new:
                    ui.button("Mark as Seen", on_click=mark_seen).props(
                        "outline no-caps dense size=md"
                    ).classes(
                        "text-slate-700 bg-white border-slate-300 hover:bg-slate-50 font-medium px-2.5 rounded"
                    )

                ui.link("Apply ↗", job_url, new_tab=True).classes(
                    "bg-blue-600 h-full hover:bg-blue-700 text-white text-sm font-medium px-3 py-1 rounded no-underline inline-block text-center"
                )
