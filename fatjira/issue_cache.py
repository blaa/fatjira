from time import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from fatjira import log
import shelve


class IssueCache:
    """
    Cache Jira issues locally for instant access.

    - Per-issue API
    - Incremental synchronization.
    """

    def __init__(self, config, jira):
        self.jira = jira
        # TODO: Shelve is slow, move to xapian? Maaaybe?
        # Reading 5000 issues from disc takes 1.2s (109MB file)
        # NOTE: for 4000 issues seem fast enough.
        self.shelve = shelve.open(config['cache_path'])

        self.issue_filter = config['issue_filter']
        self.field_filter = config['field_filter']
        self.sync_since = config['sync_since']
        self.sync_worklogs = config['sync_worklogs']

        # Totals
        self.took_worklogs = 0
        # Real time to read worklogs in parallel and store in DB
        self.took_worklogs_and_store = 0
        self.took_searches = 0
        self.total_read = 0
        self.update_start = 0

        self.pool = ThreadPoolExecutor(max_workers=config['threads'])

        assert self.field_filter is None or isinstance(self.field_filter, list)
        assert isinstance(self.issue_filter, str)

    def _parse_time(self, string):
        "Issue time into timestamp"
        time_format = '%Y-%m-%dT%H:%M:%S.000%z'
        return datetime.strptime(string, time_format).timestamp()

    def _format_time(self, ts):
        "Format timestamp into a Jira-parseable time"
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
            'last_updated': self._parse_time(self.sync_since),
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
        self.shelve.sync()
        ips = status['issues_read'] / (time() - self.update_start)
        log.info("Updating status: last_updated=%s read=%d, issues/s=%.2f",
                 self._format_time(status['last_updated']), status['issues_read'], ips)

    def update_issues(self):
        """
        Update local cache for configured projects in an incremental way.

        # TODO: Parallelize
        """
        while True:
            status = self.get_status()
            # Create query
            last_updated = self._format_time(status['last_updated'])
            query = (
                f'({self.issue_filter}) and updated >= "{last_updated}" ORDER BY updated ASC'
            )
            for page_no, page in self._read_pages(query):
                if not page:
                    self.update_status(issues_update_ts=time())
                    return

                start = time()
                if self.sync_worklogs:
                    log.info("Synchronizing worklogs for %d issues on a page",
                             len(page))
                    # Timeout is huge to only kill hunged --update automats.
                    page = self.pool.map(self.read_worklogs, page,
                                         timeout=30 + len(page) * 20)

                for i, issue in enumerate(page):
                    raw = issue.raw
                    # TODO: Compare existing entries with new ones to update stats better.
                    self.shelve[issue.key] = raw
                    status['issues_read'] += 1
                    status['last_updated'] = self._parse_time(issue.fields.updated)
                    if i % 20 == 0:
                        # Store periodically; reading worklogs can take a lot of time.
                        self.update_status(issues_read=status['issues_read'],
                                           last_updated=status['last_updated'])

                self.update_status(issues_read=status['issues_read'],
                                   last_updated=status['last_updated'])
                self.took_worklogs_and_store += time() - start

    def read_worklogs(self, issue):
        """
        Read worklogs for a given issue and add to raw data.

        Watchout: this can be executed in parallel.
        """
        if issue.fields.timespent is None or issue.fields.timespent == 0:
            return issue

        start = time()
        worklogs = self.jira.link.worklogs(issue.key)
        self.took_worklogs += time() - start
        # Simulate a structure jira module normally uses when
        # reading worklogs.
        # FIXME: This returns a lot of unnecessary information.
        issue.raw['fields']['worklog'] = {
            'total': len(worklogs),
            'worklogs': [
                worklog.raw
                for worklog in worklogs
            ]
        }
        return issue

    def update_fields(self):
        """
        Update field cache.
        """
        fields = self.jira.link.fields()
        self.shelve['_fields'] = fields
        self.update_status(fields_update_ts=time())

    def update(self):
        "Full update"
        try:
            if self.jira.link is None:
                return False
            self.update_start = time()
            self.update_fields()
            self.update_issues()
            log.info("Field and issue update took %.2f", time() - self.update_start)
        finally:
            self.shelve.sync()

        return True

    def _read_pages(self, query, page_size=250, pages=8):
        """
        Read multiple pages from a single query. It must return more data using an
        iterator that might be bulk-changed within the same minute. Otherwise
        the updating might be stuck on the same part of data.
        """
        start_at = 0
        for page in range(pages):
            log.info("Reading issues page=%d page_offset=%d size=%d",
                     page, start_at, page_size)
            start = time()
            results = self.jira.link.search_issues(query,
                                                   maxResults=page_size,
                                                   startAt=start_at,
                                                   fields=self.field_filter)
            self.took_searches += time() - start
            start_at += len(results)
            self.total_read += len(results)
            yield (page, results)
            log.info("Stat: %d read; searches %.2fs worklogs/store %.2fs "
                     "worklog_read %.2fs thread",
                     self.total_read, self.took_searches,
                     self.took_worklogs_and_store, self.took_worklogs)
            # NOTE: Yield empty page at least once to denote that there's no more
            # data in this query.
            if not results:
                break

    def issue_list(self):
        "Keys of all cached issues"
        return [
            key
            for key in self.shelve.keys()
            if not key.startswith("_")
        ]

    def get_raw(self, key):
        return self.shelve.get(key, None)
