# (C) 2020 by Tomasz bla Fortuna
# License: MIT

from collections import namedtuple


Entry = namedtuple('Entry', ['key', 'desc', 'action'])


class _State:
    def __init__(self):
        # {'k' -> action_to_call(), ...} - for lookup
        self.keymap = {}
        # [ ('k', action) ] - for display, in order
        self.commands = []

    def register(self, entry):
        "Register action with given keys"
        if entry.key in self.keymap:
            raise Exception(f"Key {entry.key} already is defined")

        self.commands.append(entry)
        self.keymap[entry.key] = entry.action

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

    def register(self, key, desc, action):
        """
        Register action within current state
        """
        entry = Entry(key, desc, action)
        self.state.register(entry)

    def call(self, key):
        """
        Find connected action and run it.
        """
        self.state.call(key)

    def push(self):
        "Push current keybindings away and create clean state"
        self.state_stack.append(self.state)
        self.state = _State()

    def pop(self):
        "Drop current state and recover one from state"
        assert self.state_stack
        self.state = self.state_stack.pop()

    def get_current(self):
        return self.state.commands
