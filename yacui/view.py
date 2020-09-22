# (C) 2020 by Tomasz bla Fortuna
# License: MIT

import _curses


class StopNavigation(Exception):
    "Stop display from navigating away from view"


class View:
    """
    Handle a display and related state and actions.

    Has access to self.window - a part of screen for displaying its data.
    """

    def __init__(self, app):
        self.app = app

    def tick(self):
        self.app.console.print("View tick")

    def redraw(self, wnd: _curses.window):
        raise NotImplementedError

    # Events
    def on_enter(self):
        pass

    def on_leave(self):
        """
        Can handle confirmations, unsaved changes, etc.

        Raise StopNavigation to prevent display from navigating away.

        Returns:
          False: Stop navigation and stick to this view
        """
        pass

    def on_drop(self):
        """
        View is being removed from the history
        """
