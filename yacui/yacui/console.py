# (C) 2020 by Tomasz bla Fortuna
# License: MIT

import curses
import curses.textpad

from yacui import keyparser


class Console:
    """
    Curses facade.
    """

    def __init__(self, debug=False):
        """
        Args:
          resize_callback: Called when resize is detected to redraw view
          debug: creates additional window split to display any debugging info.
        """
        self.stdscr = None
        self.debug = debug

        self.wnd_view = None
        self.wnd_discovery = None
        self.wnd_status = None
        self.wnd_debug = None
        # Cursor mode should be persistent across cleanup/start
        self.cursor_visible = 0

    def start(self):
        "Configure terminal options for ncurses app"

        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.halfdelay(5)
        curses.start_color()
        curses.use_default_colors()
        assert curses.has_colors()
        curses.curs_set(self.cursor_visible)
        self.stdscr.keypad(1)
        self._start_windows()

    def set_cursor(self, enabled):
        if enabled:
            self.cursor_visible = 1
            curses.curs_set(1)
        else:
            self.cursor_visible = 0
            curses.curs_set(0)

    def cleanup(self):
        "'Fix' terminal before quitting"
        curses.nocbreak()
        self.stdscr.keypad(0)
        curses.echo()
        curses.endwin()

    def start_shell(self):
        # TODO
        from IPython import embed
        try:
            self.cleanup()
            embed()
        finally:
            self.start()

    def _start_windows(self):
        lines, cols = self.stdscr.getmaxyx()
        # Configuration
        lines_discovery = 5
        lines_status = 1

        if not self.debug:
            lines_debug = 0
        else:
            # Use at most 10 lines for debug, and decrease on small screens.
            lines_debug = min(10, int(0.2 * lines))
            lines_debug = max(lines_debug, 3)

        lines_view = lines - lines_status - lines_discovery - lines_debug

        self.wnd_view = curses.newwin(lines_view, cols, 0, 0)

        if self.debug:
            self.wnd_debug = curses.newwin(lines_debug, cols, lines_view, 0)

        self.wnd_discovery = curses.newwin(lines_discovery, cols,
                                           lines_view + lines_debug, 0)

        self.wnd_status = curses.newwin(lines_status, cols,
                                        lines_view + lines_discovery + lines_debug, 0)

    def get_key(self):
        """
        Read key with half-delay and decode special combinations like Control and
        Meta keys.
        """
        return keyparser.get_key(self.wnd_view)

    def resize(self):
        "Handle resize event"

        if not self.stdscr:
            return

        # Cleanup.
        self.stdscr.erase()
        self.stdscr.refresh()

        # Create new windows in new size.
        self._start_windows()

    def query_string(self, prompt):
        "Query for a string using a textpad"
        # FIXME: Readline would be better

        # Show prompt
        self.wnd_status.erase()
        self.wnd_status.addstr(0, 0, prompt)
        self.wnd_status.refresh()

        # Create textpad
        lines, cols = self.stdscr.getmaxyx()
        start = len(prompt)

        tmp_win = curses.newwin(1, cols - start, lines-1, start)
        text_box = curses.textpad.Textbox(tmp_win, insert_mode=True)
        curses.curs_set(1)
        input_string = text_box.edit()
        curses.curs_set(0)

        # Hard to distinguish between accepted string and cancelled...
        input_string = input_string.strip()

        # Cleanup
        self.wnd_status.erase()
        self.wnd_status.refresh()
        return input_string

    def query_bool(self, prompt):
        "Query for a yes/no answer"
        self.wnd_status.erase()
        self.wnd_status.addstr(0, 0, prompt + " (y/n)")
        self.wnd_status.refresh()
        status = False
        # Leave halfdelay mode
        curses.cbreak()
        while True:
            key = self.wnd_status.getkey()
            if key in {'y', 'Y'}:
                status = True
                break
            elif key in {'n', 'N'}:
                break
        self.wnd_status.erase()
        self.wnd_status.refresh()
        curses.halfdelay(5)
        return status
