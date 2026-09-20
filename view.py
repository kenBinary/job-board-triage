from nicegui import ui

from src.view.filter_bar import filter_bar_view
from src.view.header import header_view
from src.view.job_list import job_list_view


@ui.page("/")
def index():
    ui.query("body").classes("bg-[#f8fafc] text-slate-800")

    def refresh_all():
        header_view.refresh()
        job_list_view.refresh()

    def refresh_job_list():
        job_list_view.refresh()

    with ui.column().classes("w-full max-w-7xl mx-auto p-4 md:p-6 gap-3"):
        header_view(on_job_board_change=refresh_job_list)
        filter_bar_view(on_filter_changed=job_list_view.refresh)
        job_list_view(on_status_change=refresh_all, on_page_change=refresh_job_list)


ui.run(title="Job Board Triage Engine", port=8080)
