# (C) 2020 by Tomasz bla Fortuna
# License: MIT

import curses


def _decode_ctrl(key):
    """
    Convert control codes ("\x01" - "\x1A") into ascii representation C-x
    """
    assert len(key) == 1
    if key == '\n':
        return 'RET'
    code = ord(key)
    if not 0 < code <= 0x1A:
        # Not control code
        return key
    letter = code + ord('a') - 1
    return ("C-" + chr(letter)).replace("C-i", "TAB")


def _parse_meta_o(wnd):
    "Parse escape codes starting with M-o"
    try:
        code = _decode_ctrl(wnd.get_wch())
    except curses.error:
        return "M-S-o"
    mapping = {
        'P': 'F1',
        'Q': 'F2',
        'R': 'F3',
        'S': 'F4',
    }
    key = mapping.get(code)
    if not key:
        # FIXME: Multiple presses of M-S-o will fail here.
        raise Exception(f"Unable to parse escape code '{code}'")
    return key


def _parse_escape_codes(wnd):
    # Decode escape codes
    # M-[ X ~ -> Some key ; ~ is optional.
    # M-[ 3 ~ -> Delete
    # 2 -> Insert
    # 1 -> Home, 4 -> End
    # 5 -> PageUp, 6 -> PageDown
    # M-[ A -> Up; B -> Down; C -> Right; D -> Left
    single_map = {
        'A': 'UP',
        'B': 'DOWN',
        'C': 'RIGHT',
        'D': 'LEFT',
    }
    read_code = ""
    while True:
        try:
            key = wnd.get_wch()
            if key in single_map:
                return single_map[key]
            if key == "~":
                if not read_code:
                    raise Exception("Invalid escape code")
                break
            read_code += key
        except curses.error:
            if not read_code:
                return 'M-['
            else:
                raise Exception(f"Invalid escape code M-[ {read_code}")

    tilde_map = {
        '1': 'HOME',
        '2': 'INS',
        '3': 'DELETE',
        '4': 'END',
        '5': 'PGUP',
        '6': 'PGDOWN',
        '15': 'F5',
        '17': 'F6',
        '18': 'F7',
        '19': 'F8',
        '20': 'F9',
        '21': 'F10',
        '23': 'F11',
        '24': 'F12',
    }
    prefix = ""
    if ";" in read_code:
        read_code, mod = read_code.split(';')
        mod_map = {
            "3": "M-",
            "5": "C-",
        }
        prefix = mod_map.get(mod, "")

    key = tilde_map.get(read_code)
    if key:
        return prefix + key
    raise Exception(f"Invalid escape code multi-code: {read_code}")


def _parse_meta_escape(wnd):
    # Decode escape
    try:
        key = _decode_ctrl(wnd.get_wch())
        if len(key) == 1 and key[0].isupper():
            key = "S-" + key.lower()
        key = ('M-' + key).replace('M-C-', 'C-M-')
    except curses.error:
        # Just escape
        return 'ESC'

    if key == "M-S-o":
        return _parse_meta_o(wnd)

    if key != 'M-[':
        return key

    return _parse_escape_codes(wnd)


def get_key(wnd):
    """
    Read key with half-delay and decode special combinations like Control and
    Meta keys.

    FIXME: This will cause a small delay when typing escape or M-[. Could
    be done better.
    """
    ESC = '\x1b'
    try:
        key = _decode_ctrl(wnd.get_wch())
    except curses.error:
        return None

    if key == '\x7f':
        return 'BACKSPACE'
    elif key != ESC:
        return key
    return _parse_meta_escape(wnd)
