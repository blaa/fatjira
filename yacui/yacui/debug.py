# (C) 2020 by Tomasz bla Fortuna
# License: MIT

import curses
import _curses


class DebugWindow:
    "Render debug window"

    def __init__(self, app):
        self.app = app
        self._logs = []

    def redraw(self, wnd: _curses.window):
        "Refresh debug window"
        lines, cols = wnd.getmaxyx()
        wnd.erase()
        wnd.hline(0, 0, curses.ACS_HLINE, cols)

        self._logs = self._logs[-(lines-1):]
        line = 1
        for log in self._logs:
            wnd.addstr(line, 0, log[:cols-1])
            line += 1

        wnd.refresh()

    def log(self, message):
        self._logs.append(message)
        self._logs = self._logs[-20:]
