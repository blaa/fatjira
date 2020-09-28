# (C) 2020 by Tomasz bla Fortuna
# License: MIT

from collections import namedtuple


Entry = namedtuple('Entry', ['keys', 'desc', 'action'])


class _State:
    def __init__(self):
        # {'k': action_to_call(), "C-F": action(), ...} - for lookup
        self.keymap = {}
        # [ entry1, entry2 ] - for display, in order.
        self.commands = []
        # ["Type to search", "See manual page 34", ...]
        self.hints = []

    def register(self, entry):
        "Register action with given keys"
        for key in entry.keys:
            if key in self.keymap:
                raise Exception(f"Key {key} already is defined")
            self.keymap[key] = entry.action

        self.commands.append(entry)

    def add_hint(self, hint):
        "Register a hint for a user"
        self.hints.append(hint)

    def call(self, key):
        action = self.keymap.get(key)
        if action is None:
            return False
        action()
        return True


class Bindings:
    """
    Handle keybindings registration, resolving and stack.
    """

    def __init__(self, app):
        self.app = app
        self.state_stack = []
        self.state = _State()

    def register(self, keys, desc, action):
        """
        Register action within current state
        """
        if isinstance(keys, str):
            keys = [keys]
        assert isinstance(keys, list)
        entry = Entry(keys, desc, action)
        self.state.register(entry)

    def add_hint(self, hint):
        self.state.add_hint(hint)

    def call(self, key):
        """
        Find connected action and run it.
        Returns:
          True if action was found and executed, False otherwise.
        """
        return self.state.call(key)

    def push(self):
        "Push current keybindings away and create clean state"
        self.state_stack.append(self.state)
        self.state = _State()

    def pop(self):
        "Drop current state and recover one from state"
        assert self.state_stack
        self.state = self.state_stack.pop()

    def get_current(self):
        return self.state
