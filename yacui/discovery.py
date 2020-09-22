# (C) 2020 by Tomasz bla Fortuna
# License: MIT

import curses
import _curses


class Discovery:
    "Renders keybindings for user."

    def __init__(self, app):
        self.app = app

    def redraw_keys(self, wnd, line_start, line_end, col_start, margin):
        cmds = self.app.bindings.get_current()
        theme = self.app.theme

        col = col_start
        line = line_start
        max_chars = 0
        for cmd in cmds:
            if line == line_end:
                line = line_start
                col += max_chars + margin
                max_chars = 0
            max_chars = max(max_chars, len(cmd.desc) + 2)
            wnd.addstr(line, col, cmd.key, theme.DISCOVERY_KEY)
            wnd.addstr(line, col + 2, cmd.desc, theme.DISCOVERY_DESC)
            line += 1

    def redraw(self, wnd: _curses.window):
        "Refresh status and keybindings display"
        # Parameters
        line_start = 1
        margin = 10
        col_start = 3

        lines, cols = wnd.getmaxyx()
        wnd.clear()
        wnd.hline(0, 0, curses.ACS_HLINE, cols)
        self.redraw_keys(wnd, line_start, lines, col_start, margin)
        wnd.refresh()
