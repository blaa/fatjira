# TODO: Migrate to yaml.

JIRA = {
    'srv': 'https://jira.server',
    'usr': 'user.password',
    # 'None' will prompt
    'psw': None,
    # Path to CA certificate if custom.
    'crt': None,
}

ISSUES = {
    # Applied during sync. Changing might require a full resync.
    'issue_filter': 'project in (...)',
    # TODO: List of fields to sync and track
    'field_filter': None,

    # Shelve will append ".db"
    'cache_path': 'issue_cache',

    'sync_since': '1970-01-01T01:00:00.000+0000'
}
