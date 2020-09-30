"""
Utility methods for talking to Jira.
"""
import getpass

from jira import JIRA, Issue, JIRAError

from fatjira import IssueCache


class ServiceJira:
    """
    Thin wrapper on the jira class, with mappers.

    In general as high-level abstraction as feasibile, but leaky by definition
    - will use the API of the external Jira module.
    """

    def __init__(self, server_config, issue_config):
        # Link/connection to Jira.
        self.link = None
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
            self.link = JIRA(options, basic_auth=(cfg['usr'], psw),
                             max_retries=0)
            print("Logged")
        except JIRAError:
            print('Error while connecting:')
            self.link = None
            raise

    def is_connected(self):
        return self.link is not None

    def all_cached_issues(self):
        """
        Return list of all cached issues. Without refreshing.

        When operating en masse on all issues, don't wrap them in the Issue
        class. This takes 3x the time than working on raw dicts. Any code using
        raws can easily work on a raw - except for updates.
        """
        issues = [
            self.cache.get_raw(key)
            for key in self.cache.issue_list()
        ]
        return issues

    def get_issue(self, key, refresh=True):
        """
        Get a potentially cached issue. Keep Jira module API.
        TODO: Refresh before returning, unless offline mode or explicit off.

        This returns a wrapped issue for detailed work on a single issue.
        """
        assert not key.startswith("_")
        cached = self.cache.shelve.get(key, None)
        if cached is None and (refresh is False or self.jira.is_connected is False):
            return None

        issue = Issue(options={}, session=self.link, raw=cached)
        return issue
