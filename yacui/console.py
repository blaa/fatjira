# (C) 2020 by Tomasz bla Fortuna
# License: MIT

from signal import signal, SIGWINCH
import curses
import curses.textpad


class Console:
    """
    Curses facade.
    """

    def __init__(self, resize_callback=None):
        self.stdscr = None

        # TODO: Resize support is partial.
        self.resize_callback = resize_callback
        signal(SIGWINCH, self.resize)

    def start(self):
        "Configure terminal options for ncurses app"

        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.halfdelay(5)
        curses.start_color()
        curses.use_default_colors()
        assert curses.has_colors()
        curses.curs_set(0)
        self.stdscr.keypad(1)
        self._start_windows()

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
        # Configuration
        lines_discovery = 5
        lines_status = 1

        lines, cols = self.stdscr.getmaxyx()
        lines_view = lines - lines_status - lines_discovery

        self.wnd_view = curses.newwin(lines_view, cols, 0, 0)

        self.wnd_discovery = curses.newwin(lines_discovery, cols,
                                           lines_view, 0)

        self.wnd_status = curses.newwin(lines_status, cols,
                                        lines_view + lines_discovery, 0)

    def print(self, message, endl="\n"):
        # TODO: Message at bottom with a minimal time and auto clearing.
        self.stdscr.addstr(message + endl)

    def get_key(self):
        try:
            key = self.wnd_view.getkey()
            return key
        except curses.error:
            return None

    def resize(self, a, b):
        "Handle SIGWINCH signal which happens on terminal resize"
        if not self.stdscr:
            return
        y, x = self.stdscr.getmaxyx()
        self.stdscr.refresh()
        if self.resize_callback:
            self.resize_callback()

    def status(self, message):
        "Display message on the status line"
        self.wnd_status.clear()
        self.wnd_status.addstr(0, 0, message)
        self.wnd_status.refresh()

    def query_string(self, prompt):
        "Query for a string using a textpad"
        # FIXME: Readline would be better

        # Show prompt
        self.status(prompt)

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
        self.wnd_status.clear()
        self.wnd_status.refresh()
        return input_string

    def query_bool(self, prompt):
        "Query for a yes/no answer"
        self.status(prompt + " (y/n)")
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
        self.status("")
        curses.halfdelay(5)
        return status
