#!/usr/bin/env python3
# License: MIT
# 2020 (C) by Tomasz bla Fortuna

"""
An example of using yacui library API to create a simple CUI, featuring:
1. Uses two views which can be navigated.
2. Multiple actions/bindings to show key discovery
3. Multiple input types (single line string and y/n)
4. Bindings pushing/popping
5. Shared actions between views.
"""

import curses
import _curses
from yacui import App, View


class CommonView(View):
    "Shared actions on multiple views"

    def on_enter(self):
        self.app.bindings.push()
        desc = "Back" if self.app.display.view_history else "Quit"
        self.app.bindings.register("q", desc, self.action_quit)

    def on_leave(self):
        self.app.bindings.pop()

    def action_quit(self):
        "Go back to previous display or quit completely"
        if self.app.display.view_history:
            self.app.display.back()
        else:
            self.app.stop()


class SecondView(CommonView):
    "This view can be reached from the home view"

    def on_enter(self):
        super().on_enter()
        self.app.bindings.register("H", "New Home", self.action_new_home)

    def redraw(self, wnd: _curses.window):
        "Refresh the view display"
        wnd.clear()
        wnd.addstr(0, 0, "Secondary view.")

    def action_new_home(self):
        self.app.display.navigate(HomeView)


class HomeView(CommonView):
    "View displayed after the app is opened"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action_counter = 0
        self.messages = []
        self.ticks = 0

    def on_enter(self):
        super().on_enter()
        self.app.bindings.register("c", "Test click", self.action_click)
        self.app.bindings.register("f", "Query string", self.action_read)
        self.app.bindings.register("g", "Query bool", self.action_query_bool)
        self.app.bindings.register("s", "Secondary VIEW", self.action_navigate)
        self.app.bindings.register("j", "Action", self.action_click)
        self.app.bindings.register("k", "More action", self.action_click)
        self.app.bindings.register("l", "Noisiest of all", self.action_click)

    def on_leave(self):
        self.app.bindings.pop()

    def redraw(self, wnd: _curses.window):
        "Refresh the view display"
        lines, cols = wnd.getmaxyx()
        wnd.clear()

        line = 0
        wnd.addstr(line, 0, f"View screen ({self.ticks} ticks):")
        line += 1
        for i in range(0, curses.COLORS):
            wnd.addstr(line, i % cols, str(i % 10), curses.color_pair(i))
            if (i+1) % cols == 0:
                line += 1

        line += 1
        for i, message in enumerate(self.messages):
            wnd.addstr(i + line, 0, "Msg: " + message)
        wnd.refresh()

    def log_message(self, message):
        if len(self.messages) > 10:
            self.messages = []
        self.messages.append(str(message))

    def action_click(self):
        self.action_counter += 1
        self.app.console.status(f"Clicked for the {self.action_counter} times")
        message = f"{self.action_counter} click."
        self.log_message(message)
        self.app.display.redraw_view()

    def action_read(self):
        message = self.app.console.query_string("Enter some input: ")
        self.log_message(f"You've input: {message}")
        self.app.display.redraw_view()

    def action_query_bool(self):
        answer = self.app.console.query_bool("Do you want to answer?")
        self.log_message(f"You've answered: {answer}")
        self.app.display.redraw_view()

    def action_navigate(self):
        self.app.display.navigate(SecondView)

    def tick(self):
        "Called periodically, but irregularly"
        self.ticks += 1
        if self.ticks % 10 == 0:
            self.app.display.redraw_view()


def run():
    "Initialize the app and enter the main loop"
    app = App(HomeView)
    app.loop()


if __name__ == "__main__":
    run()
