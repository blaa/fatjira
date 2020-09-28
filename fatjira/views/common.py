from yacui import View


class CommonView(View):
    "Shared actions on multiple views"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_enter(self):
        self.app.bindings.push()
        desc = "Back" if self.app.display.view_history else "Quit"
        self.app.bindings.register("q", desc, self.action_quit)

    def on_leave(self):
        self.app.bindings.pop()

    def action_quit(self):
        "Go back to previous display or quit the app completely"
        if self.app.display.view_history:
            self.app.display.back()
        else:
            self.app.stop()
