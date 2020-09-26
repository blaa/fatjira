# (C) 2020 by Tomasz bla Fortuna
# License: MIT

import curses


class Default:
    "Default theme"

    def __init__(self):
        # Colors must be defined after initscr is called.
        self.color_map = {}
        self.init_colors()

        c = self.color
        self.DISCOVERY_KEY = c("yellow", curses.A_BOLD)
        self.DISCOVERY_DESC = c("white", curses.A_BOLD)
        self.DISCOVERY_HINT = c("white")

    def init_colors(self):
        "Initialize all colors"
        for i in range(0, curses.COLORS):
            curses.init_pair(i, i, -1)

        # TODO: Not really.
        if curses.COLORS != 256:
            raise Exception("Default theme requires 256 colors in terminal")

        colors = [
            'white',
            'red',
            'green',
            'yellow',
            'blue',
            'magenta',
            'cyan',
            'gray',
            'darkgrey',
        ]
        self.color_map = {
            name: curses.color_pair(i)
            for i, name in enumerate(colors)
        }

    def color(self, name, mod = 0):
        assert mod in {0, curses.A_BOLD}
        cid = self.color_map.get(name)
        if cid is None:
            raise Exception(f"Unknown color name '{name}'")

        return cid | mod



def from_file(path):
    # TODO
    pass
