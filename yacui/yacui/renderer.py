import re
import jinja2
import _curses

from yacui import log


class Renderer:
    """
    Handle Jinja2 templates.

    TODO: Handle drawing on the screen with selected part of a THEME. For
    example use XML-like escaping and do <style theme="ISSUE_KEY">in issue key
    style</style>; but maybe something simpler is possible.

    TODO: Autowrap to fit on screen.
    """

    def __init__(self, template_path):
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_path),
            autoescape=True
        )
        self.env.filters['wrap'] = self.wrap

    def render_string(self, template, **kwargs):
        template = self.env.get_template(template)
        return template.render(**kwargs)

    def on_wnd(self, wnd: _curses.window, theme, y, x, scroll, template, **kwargs):
        """
        Render template on the window.

        TODO: Styles are a bit hacky.

        Args:
          y, x: Template start position
          scroll: skip this number of initial template lines (for scrolling)
          template: path to the template
          kwargs: template arguments.
        """
        splitter = re.compile('(<theme=[_a-zA-Z0-9]+>|</theme>)')
        theme_parser = re.compile('^<theme=([_a-zA-Z0-9]+)>$')

        lines, cols = wnd.getmaxyx()
        self.max_cols = cols  # For wrap filter
        try:
            string = self.render_string(template, **kwargs)
        except jinja2.exceptions.TemplateError:
            log.exception(f"Template rendering {template} failed.")
            wnd.addstr(y, x, "*TEMPLATE RENDERING FAILED*")
            return

        style = 0
        for line in string.split("\n"):
            line = line.rstrip()
            chunks = re.split(splitter, line)
            col = x
            for chunk in chunks:
                match = re.match(theme_parser, chunk)
                if match:
                    style_name = match.groups()[0]
                    style = getattr(theme, style_name)
                    continue
                if chunk == "</theme>":
                    style = 0
                    continue
                chunk = jinja2.Markup(chunk).unescape()
                try:
                    if scroll == 0:
                        wnd.addnstr(y, col, chunk, cols - col, style)
                    col += len(chunk)
                except _curses.error:
                    # Overflow is ok at the LAST character in LAST line.
                    return

            if scroll > 0:
                scroll -= 1
            else:
                y += 1
            if y == lines:
                break

    def wrap(self, text):
        "Filter to auto wrap text to the console width."
        lines = []

        words = text.split(" ")
        cur_line = []
        cols = 0
        for word in words:
            if cols + len(word) + 1 > self.max_cols:
                lines.append(" ".join(cur_line))
                cur_line = []
                cols = 0
            cur_line.append(word)
            cols += len(word) + 1
        if cur_line:
            lines.append(" ".join(cur_line))
        return "\n".join(lines)
