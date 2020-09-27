# (C) 2020 by Tomasz bla Fortuna
# License: MIT

from yacui import View, StopNavigation


class Display:
    MAX_HISTORY = 10

    def __init__(self, app, console):
        self.app = app
        self.console = console
        self.view_current = None
        self.view_history = []

    def history_push(self):
        "Move current view to history"
        if not self.view_current:
            # Nothing to push
            return True

        # Can throw and stop navigation
        self.view_current.on_leave()

        self.view_history.append(self.view_current)
        self.view_current = None

        drop, keep = (self.view_history[:-self.MAX_HISTORY],
                      self.view_history[-self.MAX_HISTORY:])
        for dropped in drop:
            dropped.on_drop()
            del dropped
        self.view_history = keep

    def navigate(self, view):
        """
        Switch display to a new view.

        Args:
          view: a class of a view, or a pre-created instance.
        """
        try:
            self.history_push()
        except StopNavigation:
            return False

        if isinstance(view, View):
            self.view_current = view
        else:
            self.view_current = view(self.app)
        self.view_current.on_enter()
        self.redraw_view()
        return True

    def back(self):
        "Go backward to previous view"
        if not self.view_history:
            return False

        try:
            self.view_current.on_leave()
        except StopNavigation:
            return False

        self.view_current.on_drop()
        del self.view_current

        self.view_current = self.view_history.pop()
        self.view_current.on_enter()
        self.redraw_view()
        return True

    def redraw_view(self):
        self.app.discovery.redraw(self.app.console.wnd_discovery)
        self.view_current.redraw(self.app.console.wnd_view)

    def tick(self):
        """
        Ticked periodically while we are active.
        """
        if self.view_current:
            self.view_current.tick()

    def keypress(self, key):
        """
        Executed when a pressed key does not map into an action.
        """
        if self.view_current:
            self.view_current.keypress(key)
