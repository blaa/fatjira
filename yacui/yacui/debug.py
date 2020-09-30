# (C) 2020 by Tomasz bla Fortuna
# License: MIT

from time import time
import curses
import _curses


class _Timer:
    """
    Time execution and add debug entry
    """

    def __init__(self, name, debug):
        self.name = name
        self.debug = debug
        self.start = None

    def __enter__(self):
        self.start = time()

    def __exit__(self, type, value, traceback):
        took = time() - self.start
        msg = f"'{self.name}' executed in {took:.2f}"
        self.debug.log(msg)


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

    def time(self, name):
        """
        Time execution and log result.

        Usage (with --debug):

            with self.app.debug.time("Data update"):
                self.update()
        """
        return _Timer(name, self)
