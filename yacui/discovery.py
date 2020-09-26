# (C) 2020 by Tomasz bla Fortuna
# License: MIT

import curses
import _curses


class Discovery:
    "Renders keybindings for user."

    def __init__(self, app):
        self.app = app

        # Const or recalculated from window size parameters
        self.margin_column = 10
        self.margin_left = 3
        self.margin_top = 1
        self.lines_max = None
        self.cols_max = None

    def _draw_column(self, wnd, col, cmds):
        "Draw single column"
        theme = self.app.theme
        line = self.margin_top
        entries = self.lines_max - line
        cmds_in_column = cmds[0:entries]
        max_width = 0

        max_key = max(len(cmd.key) for cmd in cmds_in_column)

        for cmd in cmds_in_column:
            wnd.addstr(line, col, cmd.key, theme.DISCOVERY_KEY)
            wnd.addstr(line, col + max_key + 1, cmd.desc, theme.DISCOVERY_DESC)
            line += 1
            max_width = max(max_width, len(cmd.desc) + max_key + 1)

        return cmds[entries:], max_width

    def _draw_hints(self, wnd, col, hints):
        "Draw hints for a user"
        theme = self.app.theme
        line = self.margin_top
        entries = self.lines_max - line
        hints_in_column = hints[0:entries]
        max_width = 0

        for hint in hints_in_column:
            wnd.addstr(line, col, hint, theme.DISCOVERY_HINT)
            line += 1
            max_width = max(max_width, len(hint))
        return hints[entries:], max_width

    def redraw(self, wnd: _curses.window):
        "Refresh status and keybindings display"
        # Update size on resize events
        self.lines_max, self.cols_max = wnd.getmaxyx()
        wnd.clear()
        wnd.hline(0, 0, curses.ACS_HLINE, self.cols_max)

        cmds = self.app.bindings.get_current().commands[:]

        col = self.margin_left

        while cmds:
            cmds, max_width = self._draw_column(wnd, col, cmds)
            col += max_width + self.margin_column

        hints = self.app.bindings.get_current().hints[:]
        while hints:
            hints, max_width = self._draw_hints(wnd, col, hints)
            col += max_width + self.margin_column

        wnd.refresh()
