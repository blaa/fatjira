import _curses

from fatjira.views import CommonView


class IssueView(CommonView):
    """
    Issue view.
    """

    def __init__(self, app, key):
        super().__init__(app)
        self.key = key
        self.issue = self.app.jira.get_issue(key)
        self.scroll = 0

    def redraw(self, wnd: _curses.window):
        "Refresh the view display"
        wnd.clear()
        self.app.renderer.on_wnd(wnd, self.app.theme, 0, 0,
                                 self.scroll,
                                 "issue_view.j2",
                                 key=self.issue.key,
                                 issue=self.issue.fields)

    def on_enter(self):
        super().on_enter()
        self.app.bindings.register("w", "Worklogs", self.menu_worklog)
        self.app.bindings.register("t", "Transitions", self.menu_transitions)

        self.app.bindings.register(["n", "DOWN"], "Scroll down",
                                   self.action_scroll_down)
        self.app.bindings.register(["p", "UP"], "Scroll up",
                                   self.action_scroll_up)
        self.app.bindings.register(["N"], "Scroll down x10",
                                   self.action_scroll_down_fast)
        self.app.bindings.register(["P"], "Scroll up x10",
                                   self.action_scroll_up_fast)

    def on_leave(self):
        super().on_leave()

    def menu_worklog(self):
        self.app.bindings.push()
        self.app.bindings.register("q", "Back to issue", self.menu_back)
        self.app.bindings.register("a", "Add worklog", self.action_worklog_add)
        self.app.bindings.register("d", "Delete worklog", None)
        self.app.bindings.register("e", "Edit worklog", None)
        self.app.display.redraw_view()

    def menu_transitions(self):
        self.app.bindings.push()
        self.app.bindings.register("q", "Back to issue", self.menu_back)
        # TODO: Just an example; should be configurable; probably per project.
        self.app.bindings.register("d", "Done", None)
        self.app.bindings.register("t", "To Do", None)
        self.app.bindings.register("p", "In progress", None)
        self.app.display.redraw_view()

    def action_worklog_add(self):
        self.app.display.status("Not supported yet")

    def menu_back(self):
        self.app.bindings.pop()
        self.app.display.redraw_view()

    def action_scroll_down(self):
        self.scroll += 1
        self.app.display.redraw_view()

    def action_scroll_up(self):
        if self.scroll > 0:
            self.scroll -= 1
        self.app.display.redraw_view()

    def action_scroll_down_fast(self):
        self.scroll += 10
        self.app.display.redraw_view()

    def action_scroll_up_fast(self):
        self.scroll -= 10
        if self.scroll < 0:
            self.scroll = 0
        self.app.display.redraw_view()
