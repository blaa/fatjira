"""
Utility methods for talking to Jira.
"""
import getpass

from jira import JIRA
from jira import JIRAError


class ServiceJira:
    """
    Thin wrapper on the jira class, with mappers.

    In general as high-level abstraction as feasibile, but leaky by definition.
    """

    def __init__(self, config):
        self.jira = None
        self.config = config

    def connect(self):
        # TODO: Parallelize
        psw = self.config['psw']
        if psw is None:
            psw = getpass.getpass(f'Password for {self.config["usr"]}: ')

        options = {
            'server': self.config['srv'],
        }

        if self.config['crt']:
            options['verify'] = self.config['crt']

        try:
            print("Logging into JIRA...")
            self.jira = JIRA(options, basic_auth=(self.config['usr'], psw),
                             max_retries=0)
            print("Logged")
        except JIRAError:
            print('Error while connecting:')
            self.jira = None
            raise

    def is_connected(self):
        return self.jira is not None

