import _curses

from fatjira.views import CommonView
from fatjira.views import SearchView


class DashboardView(CommonView):
    """
    Main application view
    """

    def __init__(self, app):
        super().__init__(app)
        self.update_in_progress = False

    def redraw(self, wnd: _curses.window):
        "Refresh the view display"
        wnd.clear()
        wnd.addstr(0, 0, "Dashboard", self.app.theme.TITLE)
        if self.update_in_progress:
            wnd.addstr(2, 0, "Updating database")

    def on_enter(self):
        super().on_enter()
        self.app.bindings.register("i", "Issues", self.action_issues)
        self.app.bindings.register("U", "Update issue cache", self.action_update)

    def on_leave(self):
        super().on_leave()

    def action_issues(self):
        self.app.display.navigate(SearchView)

    def action_update(self):
        # TODO: Parallel
        self.update_in_progress = True
        self.app.display.redraw_view()
        self.app.issue_cache.update()
        self.update_in_progress = False
        self.app.issue_cache.update()
