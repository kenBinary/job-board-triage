from nicegui import ui

from src.db.database import SessionLocal
from src.kalibrr.db import update_kalibrr_details
from src.kalibrr.models.kalibrr_job_details import KalibrrJobDetails
from src.utils.date_utils import calculate_time_difference, format_date


def kalibrr_job_card(job: KalibrrJobDetails, on_refresh):
    def mark_seen():
        job.is_new = False
        with SessionLocal() as db:
            update_kalibrr_details(db, job)
        on_refresh()

    job_url = job.url or f"https://www.kalibrr.com/jobs/{job.job_id}"

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
                    if job.is_featured:
                        ui.label("FEATURED").classes(
                            "text-[10px] font-bold text-purple-800 bg-purple-100 border border-purple-200 px-1.5 py-0.2 rounded"
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

                    if job.is_company_verified:
                        ui.label("✓ Verified").classes(
                            "text-[10px] font-semibold text-blue-700 bg-blue-50 border border-blue-200/60 px-1 rounded"
                        )

                    if job.location:
                        ui.label("•")
                        ui.label(job.location)

                    if job.work_type:
                        ui.label("•")
                        ui.label(job.work_type)

                    if job.salary_shown and (job.salary_min or job.salary_max):
                        ui.label("•")
                        currency = job.salary_currency or "PHP"
                        period = f" / {job.salary_period}" if job.salary_period else ""
                        if job.salary_min and job.salary_max:
                            salary_display = f"{currency} {job.salary_min:,.0f} - {job.salary_max:,.0f}{period}"
                        elif job.salary_min:
                            salary_display = (
                                f"{currency} {job.salary_min:,.0f}+{period}"
                            )
                        else:
                            salary_display = (
                                f"{currency} up to {job.salary_max:,.0f}{period}"
                            )
                        ui.label(salary_display).classes(
                            "font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200/60 px-1.5 py-0.2 rounded text-[11px]"
                        )

                with ui.row().classes(
                    "items-center gap-1.5 text-xs text-slate-500 flex-wrap"
                ):
                    if job.is_work_from_home:
                        ui.label("Work from Home").classes(
                            "font-semibold text-blue-700 bg-blue-50 border border-blue-200/60 px-1.5 py-0.2 rounded text-[11px]"
                        )
                    elif job.is_hybrid:
                        ui.label("Hybrid").classes(
                            "font-semibold text-cyan-700 bg-cyan-50 border border-cyan-200/60 px-1.5 py-0.2 rounded text-[11px]"
                        )

                    if job.is_open_to_fresh_grads:
                        ui.label("Fresh Grads Welcome").classes(
                            "font-semibold text-violet-700 bg-violet-50 border border-violet-200/60 px-1.5 py-0.2 rounded text-[11px]"
                        )

                    if job.job_function:
                        ui.label(job.job_function).classes(
                            "bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded-full text-xs font-medium border border-slate-200 shadow-sm"
                        )

                    if job.company_industry:
                        ui.label(job.company_industry).classes(
                            "bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded-full text-xs font-medium border border-slate-200 shadow-sm"
                        )

                    if job.num_vacancies:
                        ui.label(f"{job.num_vacancies} vacancies").classes(
                            "bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded-full text-xs font-medium border border-slate-200 shadow-sm"
                        )

                    for skill in (job.skills or [])[:5]:
                        ui.label(skill).classes(
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
