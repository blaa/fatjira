import _curses

from fatjira.views import CommonView
from yacui import Binding


class IssueView(CommonView):
    """
    Issue view.

    TODO: Add offline/online indicator.
    """

    def __init__(self, app, key):
        super().__init__(app)
        self.key = key
        self.issue = self.app.jira.get_issue(key)
        self.scroll = 0
        self.fits = True

    def redraw(self, wnd: _curses.window):
        "Refresh the view display"
        wnd.clear()
        self.fits = self.app.renderer.on_wnd(wnd, self.app.theme, 0, 0,
                                             self.scroll,
                                             "issue_view.j2",
                                             key=self.issue.key,
                                             issue=self.issue.fields)

    def on_enter(self):
        super().on_enter()

        def render_callback():
            if not self.fits:
                self.app.bindings.enable(["n", "N"])
            else:
                self.app.bindings.disable(["n", "N"])

            if self.scroll:
                self.app.bindings.enable(["p", "P"])
            else:
                self.app.bindings.disable(["p", "P"])

            if self.app.jira.is_connected():
                self.app.bindings.enable(["w", "t"])
            else:
                self.app.bindings.disable(["w", "t"])

        self.app.bindings.register_all([
            Binding("w", "Worklogs", self.menu_worklog),
            Binding("t", "Transitions", self.menu_transitions),
            Binding(["n", "DOWN"], "Scroll down", self.action_scroll_down),
            Binding(["N"], "Scroll down x10", self.action_scroll_down_fast),
            Binding(["p", "UP"], "Scroll up", self.action_scroll_up),
            Binding(["P"], "Scroll up x10", self.action_scroll_up_fast),
        ], render_callback)

    def on_leave(self):
        super().on_leave()

    def menu_worklog(self):
        self.app.bindings.register_all([
            Binding("q", "Back to issue", self.menu_back),
            Binding("a", "Add worklog", self.action_worklog_add),
            Binding("d", "Delete worklog", None),
            Binding("e", "Edit worklog", None),
        ], push=True)
        self.app.display.redraw()

    def menu_transitions(self):
        self.app.bindings.register_all([
            Binding("q", "Back to issue", self.menu_back),
            # TODO: Just an example; should be configurable; probably per project.
            Binding("d", "Done", None),
            Binding("t", "To Do", None),
            Binding("p", "In progress", None),
        ], push=True)
        self.app.display.redraw()

    def action_worklog_add(self):
        self.app.display.status("Not supported yet")

    def menu_back(self):
        self.app.bindings.pop()
        self.app.display.redraw()

    def action_scroll_down(self):
        self.scroll += 1
        self.app.display.redraw()

    def action_scroll_up(self):
        if self.scroll > 0:
            self.scroll -= 1
        self.app.display.redraw()

    def action_scroll_down_fast(self):
        self.scroll += 10
        self.app.display.redraw()

    def action_scroll_up_fast(self):
        self.scroll -= 10
        if self.scroll < 0:
            self.scroll = 0
        self.app.display.redraw()
