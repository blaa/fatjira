# (C) 2020 by Tomasz bla Fortuna
# License: MIT

from collections import namedtuple


Binding = namedtuple('Binding', ['keys', 'desc', 'action'])


class _State:
    def __init__(self):
        # {'k': action_to_call(), "C-F": action(), ...} - for lookup
        self.keymap = {}
        # [ binding1, binding2 ] - for display, in order.
        self.commands = []
        # ["Type to search", "See manual page 34", ...]
        self.hints = []
        # Registered / reserved, but disabled; ({"key", "key2", ...})
        self.disabled = set()
        # Called before rendering. Can alter disable/enable states.
        self.render_callback = None

    def register(self, binding):
        "Register action with given keys"
        for key in binding.keys:
            if key in self.keymap:
                raise Exception(f"Key {key} already is defined")
            self.keymap[key] = binding.action

        self.commands.append(binding)

    def set_callback(self, cb):
        self.render_callback = cb

    def add_hint(self, hint):
        "Register a hint for a user"
        self.hints.append(hint)

    def enable(self, keys):
        "Enable keys"
        if not isinstance(keys, list):
           keys = [keys]
        for key in keys:
            assert key in self.keymap
            if key in self.disabled:
                self.disabled.remove(key)

    def disable(self, keys):
        "Disable keys"
        if not isinstance(keys, list):
           keys = [keys]
        for key in keys:
            assert key in self.keymap
            self.disabled.add(key)

    def call(self, key):
        """
        Call action bound to the key.

        Returns:
          True: If action was called or would be called if was enabled (consume key)
          False: key not bound to any action.
        """
        if key in self.disabled:
            # No action is called, but the key is "consumed" and not sent into the view.
            return True
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
        Register a single action within current state
        """
        if isinstance(keys, str):
            keys = [keys]
        assert isinstance(keys, list)
        binding = Binding(keys, desc, action)
        self.state.register(binding)

    def register_all(self, entries, render_callback=None, push=False):
        """
        Register declaratively multiple keybindings and a callback. If push is
        True, push state before definings.

        Args:
          entries: [ binding1, binding2, ... ]
        """
        if push is True:
           self.push()

        for binding in entries:
            assert isinstance(binding, Binding)
            self.state.register(binding)
        if render_callback:
            self.state.set_callback(render_callback)

    def add_hint(self, hint):
        self.state.add_hint(hint)

    def set_callback(self, render_callback):
        """
        Set a pre-render callback.

        This might be useful to enable/disable bindings based on the current
        state within the view. This is connected with a current set of
        keybindings so it's handy for views with nested keybindings.
        """
        self.state.set_callback(render_callback)

    def call(self, key):
        """
        Find connected action and run it.
        Returns:
          True if action was found, False otherwise.
        """
        return self.state.call(key)

    def enable(self, key):
        "Enable, previously disabled, key binding"
        self.state.enable(key)

    def disable(self, key):
        """
        Disable key binding.

        Disabling any bound key causes the action to be disabled.
        """
        self.state.disable(key)

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
