"""
Utility methods for talking to Jira.
"""
import getpass

from jira import JIRA
from jira import JIRAError

from fatjira import IssueCache


class ServiceJira:
    """
    Thin wrapper on the jira class, with mappers.

    In general as high-level abstraction as feasibile, but leaky by definition.
    """

    def __init__(self, server_config, issue_config):
        self.jira = None
        self.server_config = server_config
        self.cache = IssueCache(issue_config, self)

    def connect(self):
        # TODO: Parallelize
        cfg = self.server_config
        psw = cfg['psw']
        if psw is None:
            psw = getpass.getpass(f'Password for {cfg["usr"]}: ')

        options = {
            'server': cfg['srv'],
        }

        if cfg['crt']:
            options['verify'] = cfg['crt']

        try:
            print("Logging into JIRA...")
            self.jira = JIRA(options, basic_auth=(cfg['usr'], psw),
                             max_retries=0)
            print("Logged")
        except JIRAError:
            print('Error while connecting:')
            self.jira = None
            raise

    def is_connected(self):
        return self.jira is not None

