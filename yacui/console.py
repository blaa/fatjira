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

    def set_cursor(self, enabled):
        if enabled:
            curses.curs_set(1)
        else:
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

    def _decode_ctrl(self, key):
        """
        Convert control codes ("\x01" - "\x1A") into ascii representation C-x
        """
        assert len(key) == 1
        if key == '\n':
            return 'RET'
        code = ord(key)
        if not 0 < code <= 0x1A:
            # Not control code
            return key
        letter = code + ord('a') - 1
        return ("C-" + chr(letter)).replace("C-i", "TAB")

    def _parse_meta_o(self):
        "Parse escape codes starting with M-o"
        try:
            code = self._decode_ctrl(self.wnd_view.get_wch())
        except curses.error:
            return "M-S-o"
        mapping = {
            'P': 'F1',
            'Q': 'F2',
            'R': 'F3',
            'S': 'F4',
        }
        key = mapping.get(code)
        if not key:
            raise Exception(f"Unable to parse escape code {code}")
        return key

    def _parse_escape_codes(self):
        # Decode escape codes
        # M-[ X ~ -> Some key ; ~ is optional.
        # M-[ 3 ~ -> Delete
        # 2 -> Insert
        # 1 -> Home, 4 -> End
        # 5 -> PageUp, 6 -> PageDown
        # M-[ A -> Up; B -> Down; C -> Right; D -> Left
        single_map = {
            'A': 'UP',
            'B': 'DOWN',
            'C': 'RIGHT',
            'D': 'LEFT',
        }
        read_code = ""
        while True:
            try:
                key = self.wnd_view.get_wch()
                if key in single_map:
                    return single_map[key]
                if key == "~":
                    if not read_code:
                        raise Exception("Invalid escape code")
                    break
                read_code += key
            except curses.error:
                if not read_code:
                    return 'M-['
                else:
                    raise Exception(f"Invalid escape code M-[ {read_code}")

        tilde_map = {
            '1': 'HOME',
            '2': 'INS',
            '3': 'DELETE',
            '4': 'END',
            '5': 'PGUP',
            '6': 'PGDOWN',
            '15': 'F5',
            '17': 'F6',
            '18': 'F7',
            '19': 'F8',
            '20': 'F9',
            '21': 'F10',
            '23': 'F11',
            '24': 'F12',
        }
        prefix = ""
        if ";" in read_code:
            read_code, mod = read_code.split(';')
            mod_map = {
                "3": "M-",
                "5": "C-",
            }
            prefix = mod_map.get(mod, "")

        key = tilde_map.get(read_code)
        if key:
            return prefix + key
        raise Exception(f"Invalid escape code multi-code: {read_code}")

    def _parse_meta_escape(self):
        # Decode escape
        try:
            key = self._decode_ctrl(self.wnd_view.get_wch())
            if len(key) == 1 and key[0].isupper():
                key = "S-" + key.lower()
            key = ('M-' + key).replace('M-C-', 'C-M-')
        except curses.error:
            # Just escape
            return 'ESC'

        if key == "M-O":
            return self._parse_meta_o()

        if key != 'M-[':
            return key

        return self._parse_escape_codes()

    def get_key(self):
        """
        Read key with half-delay and decode special combinations like Control and
        Meta keys.

        FIXME: This will cause a small delay when typing escape or M-[. Could
        be done better.
        """
        ESC = '\x1b'

        try:
            key = self._decode_ctrl(self.wnd_view.get_wch())
        except curses.error:
            return None

        if key == '\x7f':
            return 'BACKSPACE'
        elif key != ESC:
            return key
        return self._parse_meta_escape()

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
