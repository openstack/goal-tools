#!/usr/bin/env python3

import collections
import json
import logging

from goal_tools import governance

from cliff import lister
import requests

LOG = logging.getLogger(__name__)


def decode_json(raw):
    """Trap JSON decoding failures and provide more detailed errors

    Remove ')]}' XSS prefix from data if it is present, then decode it
    as JSON and return the results.

    :param raw: Response text from API
    :type raw: str

    """

    # Gerrit's REST API prepends a JSON-breaker to avoid XSS vulnerabilities
    if raw.text.startswith(")]}'"):
        trimmed = raw.text[4:]
    else:
        trimmed = raw.text

    # Try to decode and bail with much detail if it fails
    try:
        decoded = json.loads(trimmed)
    except Exception:
        LOG.error(
            '\nrequest returned %s error to query:\n\n    %s\n'
            '\nwith detail:\n\n    %s\n',
            raw, raw.url, trimmed)
        raise
    return decoded


def query_gerrit(offset=0, only_open=True):
    """Query the Gerrit REST API"""
    url = 'https://review.openstack.org/changes/'
    query = 'topic:python3-first'
    if only_open:
        query = query + ' is:open'
    LOG.debug('querying %s %r offset %s', url, query, offset)
    raw = requests.get(
        url,
        params={
            'n': '100',
            'start': offset,
            'q': query,
            'o': [
                'ALL_REVISIONS',
                'REVIEWER_UPDATES',
                'DETAILED_ACCOUNTS',
                'CURRENT_COMMIT',
                'LABELS',
                'DETAILED_LABELS',
            ],
        },
        headers={'Accept': 'application/json'},
    )
    return decode_json(raw)


def all_changes(only_open=True):
    offset = 0
    while True:
        changes = query_gerrit(offset, only_open=only_open)

        yield from changes

        if changes and changes[-1].get('_more_changes', False):
            offset += 100
        else:
            break


def count_votes(review, group='Rollcall-Vote'):
    votes = collections.Counter()
    votes.update(
        vote.get('value')
        for vote in review['labels'].get(group, {}).get('all', [])
    )
    if None in votes:
        del votes[None]
    return votes


def format_votes(votes):
    return 'nay:{:2d} / abs:{:2d} / yes:{:2d}'.format(
        votes.get(-1, 0), votes.get(0, 0), votes.get(1, 0)
    )


def get_one_row(change):
    subject = change['subject'].rstrip()
    repo = change.get('project')
    url = 'https://review.openstack.org/{}'.format(change['_number'])
    w_status = change.get('status')
    branch = change.get('branch')
    if w_status not in ('ABANDONED', 'MERGED'):
        code_review = count_votes(change, 'Code-Review')
        verified = count_votes(change, 'Verified')
        if verified.get(-1):
            v_status = 'FAILED'
        elif verified.get(1):
            v_status = 'PASS'
        else:
            v_status = 'UNKNOWN'
        workflow = count_votes(change, 'Workflow')
        if workflow.get(-1):
            w_status = 'WIP'
        elif code_review.get(-1):
            w_status = 'negative vote'
        elif code_review.get(1):
            w_status = 'REVIEWED'
    return (subject, repo, v_status, w_status, url, branch)


class PatchesList(lister.Lister):
    "clone the repositories for a team"

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--project-list',
            default=governance.PROJECTS_LIST,
            help='URL for projects.yaml',
        )
        parser.add_argument(
            '--all',
            default=False,
            action='store_true',
            help='show all patches',
        )
        parser.add_argument(
            'team',
            help='the team name',
        )
        return parser

    def take_action(self, parsed_args):
        gov_dat = governance.Governance(url=parsed_args.project_list)
        repos = set(gov_dat.get_repos_for_team(parsed_args.team))
        LOG.debug('filtering on %s', repos)

        only_open = not parsed_args.all
        LOG.debug('only_open %s', only_open)

        changes = (
            c for c in all_changes(only_open)
            if c.get('project') in repos
        )

        rows = list(get_one_row(c) for c in changes)
        LOG.debug('rows: %s', len(rows))

        def summarize():
            counts = collections.Counter()
            for row in rows:
                counts.update({row[3]: 1})
                yield row
            yield ('', '', '', '', '', '')
            for status, n in sorted(counts.items()):
                yield ('', '', '', status, str(n), '')

        columns = ('Subject', 'Repo', 'Tests', 'Workflow', 'URL', 'Branch')
        return (columns, summarize())
