import _curses

from fatjira.views import CommonView


class IssueView(CommonView):
    """
    Issue view.
    """

    def __init__(self, app, key):
        super().__init__(app)
        self.key = key
        self.issue = self.app.jira.cache.get_issue(key)

    def redraw(self, wnd: _curses.window):
        "Refresh the view display"
        wnd.clear()
        self.app.renderer.on_wnd(wnd, self.app.theme, 0, 0,
                                 "issue_view.j2",
                                 key=self.issue["key"],
                                 issue=self.issue["fields"])

    def on_enter(self):
        super().on_enter()
        self.app.bindings.register("w", "Worklogs", self.menu_worklog)
        self.app.bindings.register("t", "Transitions", self.menu_transitions)

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
        pass

    def menu_back(self):
        self.app.bindings.pop()
        self.app.display.redraw_view()
