import logging
from datetime import datetime
from time import time
import shelve


log = logging.getLogger('issue_cache')


class IssueCache:
    """
    Cache Jira issues locally for instant access.
    """
    TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.000%z'

    def __init__(self, config, jira):
        self.jira = jira
        # TODO: Shelve is slow, move to xapian? Maaaybe?
        # NOTE: for 4000 issues seem fast enough.
        self.shelve = shelve.open(config['cache_path'])

        self.issue_filter = config['issue_filter']
        self.field_filter = config['field_filter']
        self.sync_since = config['sync_since']
        assert self.field_filter is None or isinstance(self.field_filter, list)
        assert isinstance(self.issue_filter, str)

    def parse_time(self, string):
        "Issue time into timestamp"
        return datetime.strptime(string, self.TIME_FORMAT).timestamp()

    def format_time(self, ts):
        "Format timestamp into Jira-parseable time"
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

    def load_field_mapping(self):
        "Load field mapping from shelve"
        self._fields = self.shelve['_fields']
        self._field_by_name = {field['name']: field['id'] for field in self._fields}
        self._field_by_id = {field['id']: field['name'] for field in self._fields}

    def get_status(self):
        """
        Read status from shelve, handle defaults.
        """
        status = self.shelve.get('_update_status', {
            # Date of the last issue.
            'last_updated': self.parse_time(self.sync_since),
            'issues_read': 0,

            'fields_update_ts': 0,
            'issues_update_ts': 0,
        })
        return status

    def update_status(self, **kwargs):
        """
        Update status
        """
        status = self.get_status()
        for key, value in kwargs.items():
            if key not in status:
                raise Exception(f"Status {status} doesn't have key {key} - recreate DB")
            status[key] = value
        self.shelve['_update_status'] = status
        log.info("Updating status: %r", status)

    def update_issues(self):
        """
        Update local cache for configured projects in an incremental way.

        # TODO: Parallelize
        """
        while True:
            status = self.get_status()
            # Create query
            last_updated = self.format_time(status['last_updated'])
            query = (
                f'({self.issue_filter}) and updated >= "{last_updated}" ORDER BY updated ASC'
            )

            for page_no, page in self.read_pages(query):
                if not page:
                    self.update_status(issues_update_ts=time())
                    return

                for issue in page:
                    # TODO: Compare existing entries with new ones to update stats better.
                    self.shelve[issue.key] = issue.raw
                    status['issues_read'] += 1
                    status['last_updated'] = self.parse_time(issue.fields.updated)
                    # TODO: Add worklog reading and caching

                self.update_status(issues_read=status['issues_read'],
                                   last_updated=status['last_updated'])

    def update_fields(self):
        """
        Update field cache.
        """
        fields = self.jira.fields()
        self.shelve['_fields'] = fields
        self.update_status(fields_update_ts=time())

    def update(self):
        "Full update"
        self.update_fields()
        self.update_issues()

    def read_pages(self, query, page_size=250, pages=8):
        """
        Read multiple pages from a single query. It must return more data using an
        iterator that might be bulk-changed within the same minute. Otherwise
        the updating might be stuck on the same part of data.
        """
        start_at = 0
        for page in range(pages):
            log.info("Reading query %s page_size=%d page_offset=%d", query, page, start_at)
            results = self.jira.search_issues(query,
                                              maxResults=page_size,
                                              startAt=start_at)
            start_at += len(results)
            log.info("Read %d entries", len(results))
            yield (page, results)
            # NOTE: Yield empty page at least once to denote that there's no more
            # data in this query.
            if not results:
                break

    def keys(self):
        return [
            key
            for key in self.shelve.keys()
            if not key.startswith("_")
        ]

    def get_issue(self, key, refresh=True):
        """
        TODO: Refresh before returning, unless offline mode.
        """
        return self.shelve[key]
