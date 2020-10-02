
import curses
from yacui.themes import Default


class FatjiraTheme(Default):
    def __init__(self):
        super().__init__()
        c = self.color

        self.ISSUE_KEY = c("blue", curses.A_BOLD)
        self.ISSUE_KEY_SELECTED = c("blue", curses.A_BOLD | curses.A_REVERSE)
        self.ISSUE_SUMMARY = c("white")
        self.ISSUE_SUMMARY_SELECTED = c("white", curses.A_REVERSE)
        self.USER_NAME = c("yellow", curses.A_BOLD)
        self.WORK_TIME = c("cyan", curses.A_BOLD)
        self.WORK_START = c("white", curses.A_BOLD)
