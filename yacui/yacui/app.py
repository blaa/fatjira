# (C) 2020 by Tomasz bla Fortuna
# License: MIT

import logging
import curses

from yacui import Console, Display
from yacui import Bindings, Discovery
from yacui import DebugWindow
from yacui import themes


class App:
    """
    Application backbone, holds current state.
    """

    def __init__(self, home_screen, theme_cls=None, debug=False):
        self.home_screen = home_screen

        if theme_cls is None:
            theme_cls = themes.Default
        self.theme_cls = theme_cls

        self._stop = False
        self.console = Console(debug)
        self.display = Display(self, self.console)
        self.bindings = Bindings(self)
        self.discovery = Discovery(self)
        self.debug = DebugWindow(self)

    def loop(self):
        "Main application loop"
        # NOTE: This could be migrated to asyncio with some patchy ncurses
        # getch support.
        try:
            self.console.start()
            self.theme = self.theme_cls()
            self.display.navigate(self.home_screen)

            while not self._stop:
                key = self.console.get_key()
                if key == curses.KEY_RESIZE:
                    # TODO: Doesn't work yet.
                    # SIGWINCH might be necessary but works half-the-way still.
                    self.console.resize()
                    self.display.redraw()
                elif key is None:
                    self.display.tick()
                else:
                    found = self.bindings.call(key)
                    if not found:
                        self.display.keypress(key)
        except KeyboardInterrupt:
            self.console.cleanup()
            log.exception("User request, logging traceback for debugging")
            print("Quit on user request")
        except Exception:
            raise
        finally:
            self.console.cleanup()

    def stop(self):
        "Called by views to schedule application stop"
        self._stop = True
