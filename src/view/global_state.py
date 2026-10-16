from typing import Literal


class GlobalState:
    job_board: Literal[
        "Jobstreet",
        "Indeed",
        "OLJ",
        "Mynimo",
        "Kalibrr",
        "LinkedIn",
        "LinkedIn Posts",
        "Facebook",
    ]

    def __init__(self):
        self.job_board = "Jobstreet"
        self.show_new_only = True


global_state = GlobalState()
