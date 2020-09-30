import os
import logging
import argparse
from yacui import App, Renderer
from fatjira.views import DashboardView, SearchView
from fatjira import ServiceJira
from fatjira import FatjiraTheme


import config


def setup_logging():
    "Don't clobber the ncurses stdout with logs"
    logging.basicConfig(filename="fatjira.log", level=logging.INFO)


def parse_args():
    p = argparse.ArgumentParser()
    # TODO: CLI?
    p.add_argument("--remote-status",
                   help="",
                   action="store_true")

    p.add_argument("--remote-report",
                   help="",
                   action="store_true")

    p.add_argument("--offline",
                   help="Work offline, without connecting",
                   action="store_true")

    p.add_argument("--debug",
                   help="Enable additional debugging",
                   action="store_true")

    p.add_argument("--shell",
                   help="Open shell with available jira object",
                   action="store_true")

    p.add_argument("--update",
                   help="Update local issue cache",
                   action="store_true")

    args = p.parse_args()
    return args, p


def shell(app):
    "Run shell with access to important variables"
    from IPython import embed
    jira = app.jira
    cache = app.issue_cache
    print("Available: jira, app, cache")
    embed()


def main():
    "Initialize the app and enter the main loop"
    args, p = parse_args()

    # Connect to Jira first. FIXME: Do it lazily in background
    setup_logging()
    jira_service = ServiceJira(config.JIRA, config.ISSUES)
    if not args.offline:
        jira_service.connect()

    app = App(DashboardView, theme_cls=FatjiraTheme, debug=args.debug)
    app.config = config
    app.jira = jira_service

    # Template renderer
    here = os.path.dirname(os.path.realpath(__file__))
    template_path = os.path.join(here, "templates")
    app.renderer = Renderer(template_path)

    if args.update:
        if args.offline:
            print("Unable to update while offline")
            return
        logging.info("Executing update from CLI")
        jira_service.cache.update()
        return
    elif args.shell:
        logging.info("Executing shell")
        return shell(app)

    return app.loop()
