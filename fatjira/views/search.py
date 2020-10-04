import _curses

from yacui import View
from fatjira import IncrementalSearch
from fatjira.views import IssueView


def extract_issue(issue):
    "Experimental issue extractor"
    f = issue['fields']
    parts = [
        issue['key'],
        "k=" + issue['key'],
        f['summary'] or "",
        f['description'] or "",
        "@" + f['assignee']['name'] if f['assignee'] else "none",
        "rep=" + f['reporter']['name'] if f['reporter'] else "none",
        "st=" + f['status']['name'].upper().replace(" ", ""),
        "t=" + f['issuetype']['name'],
        # Components?
    ]
    return " ".join(parts)


class SearchView(View):
    """
    Main application view
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Index is not "sticky" when selection changes.
        self.selected_idx = 0
        self.query = ""
        self.results = []

        # TEMP
        with self.app.debug.time("Load all issues"):
            self.all_issues = self.app.jira.all_cached_issues()
        with self.app.debug.time("Initiate search"):
            self.search = IncrementalSearch(self.all_issues, extract_issue)

    def _update_search_state(self):
        self.search.search(self.query)
        self.results = self.search.get_results()
        if self.selected_idx > len(self.results):
            self.selected_idx = len(self.results)
        self.app.debug.log("cached queries:" + repr(list(self.search.cache.keys())))

    def redraw(self, wnd: _curses.window):
        "Refresh the view display"
        lines, cols = wnd.getmaxyx()
        wnd.erase()
        msg = "Incremental search: " + self.query
        wnd.addstr(0, 0, msg)
        cursor_position = len(msg)

        self._update_search_state()

        msg = "{}/{}".format(len(self.results), len(self.all_issues))
        wnd.addstr(0, cols - len(msg), msg)

        if self.selected_idx >= len(self.results):
            self.selected_idx = max(0, len(self.results) - 1)

        line = 1
        max_summary = cols - 10 - 5
        for i, result in enumerate(self.results):
            if i == self.selected_idx:
                th_key = self.app.theme.ISSUE_KEY_SELECTED
                th_summary = self.app.theme.ISSUE_SUMMARY_SELECTED
            else:
                th_key = self.app.theme.ISSUE_KEY
                th_summary = self.app.theme.ISSUE_SUMMARY

            # TODO: Unified table generator
            j = result['fields']
            summary = j["summary"]
            if len(summary) > max_summary:
                summary = summary[:max_summary] + "…"
            summary += " " * (cols - len(summary) - 16)
            msg = f"{result['key']:10s} {summary}"
            wnd.addstr(line, 0, "{:15}".format(result['key']), th_key)
            wnd.addstr(line, 15, summary[:cols - 15 - 1], th_summary)
            line += 1
            if line == lines:
                break

        wnd.move(0, cursor_position)

    def on_enter(self):
        self.app.bindings.push()
        self.app.bindings.register("M-q", "Back", self.app.display.back)
        self.app.bindings.register("RET", "Select", self.action_select)
        self.app.bindings.register(["C-n", "DOWN"], "Next", self.action_next)
        self.app.bindings.register(["C-p", "UP"], "Previous", self.action_prev)
        self.app.bindings.add_hint("Type to search incrementally")
        self.app.bindings.add_hint("@assignee, rep=reporter, st=status")
        self.app.bindings.add_hint("k=key t=type")
        msg = "You are " + ("online" if self.app.jira.is_connected() else "offline")
        self.app.bindings.add_hint(msg)

        self.app.console.set_cursor(True)

    def on_leave(self):
        self.app.bindings.pop()
        self.app.console.set_cursor(False)

    def action_select(self):
        # Get selected issue
        if not self.results:
            self.app.display.status("No issue selected.")
            return

        try:
            result = self.results[self.selected_idx]
        except IndexError:
            self.selected_idx = 0
            self.app.display.redraw()
            return
        key = result['key']
        view = IssueView(self.app, key)
        self.app.display.navigate(view)

    def action_next(self):
        self.selected_idx += 1
        self.app.display.redraw()

    def action_prev(self):
        self.selected_idx = max(0, self.selected_idx - 1)
        self.app.display.redraw()

    def keypress(self, key):
        # TODO: Move to shared editor
        if key == "BACKSPACE":
            self.query = self.query[:-1]
        elif key == "M-BACKSPACE":
            # Delete last word.
            pos = self.query.rstrip().rfind(" ")
            if pos == -1:
                pos = 0
            else:
                pos += 1
            self.query = self.query[:pos]
        elif len(key) == 1:
            self.query += key
        else:
            self.app.debug.log(f"Unhandled key: {key}")

        self.app.display.redraw()
