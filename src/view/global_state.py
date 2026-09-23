from typing import Literal


class GlobalState:
    job_board: Literal["Jobstreet", "Indeed", "OLJ"]

    def __init__(self):
        self.job_board = "Jobstreet"
        self.show_new_only = True


global_state = GlobalState()
