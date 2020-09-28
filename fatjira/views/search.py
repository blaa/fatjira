import _curses

from yacui import View
from fatjira import IncrementalSearch

def extract_issue(issue):
    "Experimental issue extractor"
    if 'fields' not in issue:
        raise Exception(issue)
    f = issue['fields']
    parts = [
        issue['key'],
        "k=" + issue['key'],
        f['summary'] or "",
        f['description'] or "",
        "@" + f['assignee']['name'] if f['assignee'] else "none",
        "rep=" + f['reporter']['name'] if f['reporter'] else "none",
        "st=" + f['status']['name'].upper().replace(" ", ""),
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
        issue_keys = [
            key
            for key in self.app.issue_cache.shelve.keys()
            if not key.startswith("_")
        ]
        self.all_issues = [
            self.app.issue_cache.shelve[key]
            for key in issue_keys
        ]
        self.search = IncrementalSearch(self.all_issues, extract_issue)
                                        #IncrementalSearch.recursive_extract_fn)

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
        self.app.bindings.register("C-g", "Back", self.app.display.back)
        self.app.bindings.register("RET", "Select", self.action_select)
        self.app.bindings.register(["C-n", "DOWN"], "Next", self.action_next)
        self.app.bindings.register(["C-p", "UP"], "Previous", self.action_prev)
        self.app.bindings.add_hint("Type to search incrementally")
        self.app.console.set_cursor(True)

    def on_leave(self):
        self.app.bindings.pop()
        self.app.console.set_cursor(False)

    def action_select(self):
        self.app.console.status("SELECTED")
        self.app.display.redraw_view()

    def action_next(self):
        self.selected_idx += 1
        self.app.display.redraw_view()

    def action_prev(self):
        self.selected_idx -= 1
        self.app.display.redraw_view()

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

        self.app.display.redraw_view()
