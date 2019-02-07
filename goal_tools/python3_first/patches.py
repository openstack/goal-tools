#!/usr/bin/env python3

import collections
import json
import logging
import os.path

import appdirs
from cliff import lister
import requests

from goal_tools import governance
from goal_tools import storyboard

LOG = logging.getLogger(__name__)
BATCH_SIZE = 300


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


def query_gerrit(offset=0, only_open=True, extra_query=''):
    """Query the Gerrit REST API"""
    url = 'https://review.openstack.org/changes/'
    query = 'topic:python3-first'
    if only_open:
        query = query + ' is:open'
    if extra_query:
        query = query + ' ' + extra_query
    LOG.debug('querying %s %r offset %s', url, query, offset)
    raw = requests.get(
        url,
        params={
            'n': str(BATCH_SIZE),
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


def all_changes(only_open=True, extra_query=''):
    offset = 0
    while True:
        changes = query_gerrit(offset, only_open=only_open,
                               extra_query=extra_query)

        yield from changes

        if changes and changes[-1].get('_more_changes', False):
            offset += BATCH_SIZE
        else:
            LOG.debug('total of %d patches', offset + len(changes))
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


def get_one_row(change, gov_dat):
    subject = change['subject'].rstrip()
    repo = change.get('project')
    url = 'https://review.openstack.org/{}'.format(change['_number'])
    branch = change.get('branch')
    owner = change.get('owner', {}).get('name', 'UNKNOWN')
    if '_TEAM' in change:
        team = change['_TEAM']
    else:
        team = gov_dat.get_repo_owner(repo) or 'unknown'

    v_status = 'UNKNOWN'
    verified = count_votes(change, 'Verified')
    if verified.get(-1) or verified.get(-2):
        v_status = 'FAILED'
    elif verified.get(1):
        v_status = 'PASS'
    elif verified.get(2):
        v_status = 'VERIFIED'

    w_status = change.get('status')
    if w_status not in ('ABANDONED', 'MERGED'):
        code_review = count_votes(change, 'Code-Review')
        workflow = count_votes(change, 'Workflow')
        if workflow.get(-1):
            w_status = 'WIP'
        elif workflow.get(1):
            w_status = 'APPROVED'
        elif code_review.get(-1) or code_review.get(-2):
            w_status = 'negative vote'
        elif code_review.get(1) or code_review.get(2):
            w_status = 'REVIEWED'

    return (subject, repo, team, v_status, w_status, url, branch, owner)


class PatchesList(lister.Lister):
    "list the patches proposed for a team or repository"

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
            '--imports',
            default=False,
            action='store_true',
            help='show only zuul imports, not follow-ups',
        )
        parser.add_argument(
            '--repo',
            help='only the patches for the given repository',
        )
        parser.add_argument(
            'team',
            nargs='?',
            help='the team name',
        )
        return parser

    _import_subject = 'import zuul job settings from project-config'

    def take_action(self, parsed_args):
        gov_dat = governance.Governance(url=parsed_args.project_list)

        only_open = not parsed_args.all
        LOG.debug('only_open %s', only_open)

        changes = all_changes(only_open)

        if parsed_args.team:
            repos = set(gov_dat.get_repos_for_team(parsed_args.team))
            LOG.debug('filtering on %s', repos)
            changes = (
                c for c in changes
                if c.get('project') in repos
            )

        if parsed_args.repo:
            changes = (
                c for c in changes
                if c.get('project') == parsed_args.repo
            )

        if parsed_args.imports:
            changes = (
                c for c in changes
                if c.get('subject') == self._import_subject
            )

        rows = list(get_one_row(c, gov_dat) for c in changes)
        LOG.debug('rows: %s', len(rows))

        if not parsed_args.repo and not parsed_args.imports:
            LOG.debug('looking for cleanup changes')
            cleanup_changes = get_cleanup_changes_by_team()
            to_add = []
            if parsed_args.team:
                if parsed_args.team.lower() in cleanup_changes:
                    to_add.append(cleanup_changes[parsed_args.team.lower()])
            else:
                for team, change in cleanup_changes.items():
                    change['_TEAM'] = team
                    to_add.append(change)
            if to_add:
                if only_open:
                    to_add = (
                        c
                        for c in to_add
                        if c.get('status') not in ('MERGED', 'ABANDONED')
                    )
                extra_rows = (
                    get_one_row(c, gov_dat)
                    for c in to_add
                )
                rows.extend(extra_rows)

        rows = sorted(rows, key=lambda r: (r[1], r[5], r[4]))

        if parsed_args.team:
            columns = ('Subject', 'Repo',
                       'Tests', 'Workflow', 'URL', 'Branch', 'Owner')
            data = (
                r[:2] + r[3:]
                for r in rows
            )
        else:
            columns = ('Subject', 'Repo', 'Team',
                       'Tests', 'Workflow', 'URL', 'Branch', 'Owner')
            data = rows
        return (columns, data)


def search_cleanup_patches(offset=0):
    """Query the Gerrit REST API"""
    url = 'https://review.openstack.org/changes/'
    query = ' '.join([
        'project:openstack-infra/project-config',
        'message:"remove job settings"',
        'topic:python3-first',
    ])
    LOG.debug('querying %s %r offset %s', url, query, offset)
    raw = requests.get(
        url,
        params={
            'n': str(BATCH_SIZE),
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


def get_cleanup_changes():
    offset = 0
    while True:
        changes = search_cleanup_patches(offset)

        yield from changes

        if changes and changes[-1].get('_more_changes', False):
            offset += BATCH_SIZE
        else:
            break


def get_cleanup_changes_by_team():
    LOG.debug('finding cleanup patches in project-config')
    prefix = 'remove job settings for'
    suffix = 'repositories'
    cleanup_changes = {}
    for change in get_cleanup_changes():
        subject = change.get('subject', '').lower()
        if subject.startswith(prefix):
            subject = subject[len(prefix):]
        if subject.endswith(suffix):
            subject = subject[:-1 * len(suffix)]
        subject = subject.strip()
        cleanup_changes[subject] = change
    return cleanup_changes


class PatchesCount(lister.Lister):
    "count the patches open for each team"

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        config_dir = appdirs.user_config_dir('OSGoalTools', 'OpenStack')
        config_file = os.path.join(config_dir, 'storyboard.ini')
        parser.add_argument(
            '--config-file',
            default=config_file,
            help='storyboard configuration file (%(default)s)',
        )
        parser.add_argument(
            '--project-list',
            default=governance.PROJECTS_LIST,
            help='URL for projects.yaml',
        )
        parser.add_argument(
            '--minimal', '-m',
            default=False,
            action='store_true',
            help='show less info for narrower report',
        )
        parser.add_argument(
            '--only-open', '-o',
            default=False,
            action='store_true',
            help='only show teams with open patches',
        )
        return parser

    _import_subject = 'import zuul job settings from project-config'
    _url_base = 'https://review.openstack.org/#/c/'

    _subjects = [
        # ('zuul', ['import zuul job settings from project-config']),
        ('tox defaults', ['fix tox python3 overrides']),
        ('Docs', ['switch documentation job to new PTI']),
        ('3.6 unit', ['add python 3.5 unit test job',
                      'add python 3.6 unit test job']),
    ]

    def take_action(self, parsed_args):
        gov_dat = governance.Governance(url=parsed_args.project_list)
        sb_config = storyboard.get_config(parsed_args.config_file)

        LOG.debug('finding champion assignments')
        sbc = storyboard.get_client(sb_config)
        story = sbc.stories.get(id='2002586')
        assignments = {}
        for task in story.tasks.get_all():
            if task.assignee_id:
                user = sbc.users.get(id=task.assignee_id)
                assignments[task.title] = user.full_name
            else:
                assignments[task.title] = ''

        cleanup_changes = get_cleanup_changes_by_team()

        changes = all_changes(False)

        # We aren't going to migrate the settings for the infra team.
        interesting_teams = gov_dat.get_teams()
        interesting_teams.remove('Infrastructure')
        # The loci team had no work to do.
        interesting_teams.remove('loci')

        count_init = {
            team: 0
            for team in interesting_teams
        }
        team_counts = {
            title: collections.Counter(count_init)
            for title, subject in self._subjects
        }
        open_counts = {
            title: collections.Counter(count_init)
            for title, subject in self._subjects
        }
        unreviewed_counts = collections.Counter(count_init)
        fail_counts = collections.Counter(count_init)

        subject_lookup = {
            subject: title
            for title, subject_list in self._subjects
            for subject in subject_list
        }
        all_titles = tuple(t for t, s in self._subjects)

        LOG.debug('counting in-tree changes')
        for c in changes:
            status = c.get('status')
            if status == 'ABANDONED':
                continue
            item = {gov_dat.get_repo_owner(c.get('project')) or 'other': 1}
            title = subject_lookup.get(c.get('subject'))
            if not title:
                continue
            team_counts[title].update(item)
            if c.get('status') != 'MERGED':
                open_counts[title].update(item)
                verified_votes = count_votes(c, 'Verified')
                if verified_votes.get(-1) or verified_votes.get(-2):
                    fail_counts.update(item)
                # We count reviewers as anyone posting +/- 1 or +/- 2
                # votes on a patch.
                reviewed_votes = count_votes(c, 'Code-Review')
                reviewers = (
                    sum(reviewed_votes.values()) - reviewed_votes.get(0, 0)
                )
                if not reviewers:
                    unreviewed_counts.update(item)

        columns = (
            ('Team',) +
            all_titles +
            ('Failing',
             'Unreviewed',
             'Total',
             'Champion')
        )

        def get_done_value(title, team, done_msg='+'):
            if title != 'zuul':
                return done_msg
            if not team_counts['zuul'][team]:
                n_repos = len(list(gov_dat.get_repos_for_team(team)))
                return 'not started, {} repos'.format(n_repos)
            cleanup = cleanup_changes.get(team.lower())
            if not cleanup:
                return 'cleanup patch not found'
            workflow_votes = count_votes(cleanup, 'Workflow')
            if cleanup.get('status') == 'MERGED':
                return done_msg
            if open_counts['zuul'][team]:
                return 'in progress'
            if workflow_votes.get(-1):
                if parsed_args.minimal:
                    return 'ready for cleanup'
                return 'need to remove WIP from {}{}'.format(
                    self._url_base, cleanup.get('_number'))
            if parsed_args.minimal:
                return 'waiting for cleanup'
            return 'waiting for cleanup {}{}'.format(
                self._url_base, cleanup.get('_number'))

        def format_count(title, team, done_msg='+'):
            oc = open_counts[title].get(team, 0)
            tc = team_counts[title].get(team, 0)
            if tc:
                if oc:
                    return '{:3}/{:3}'.format(oc, tc)
                return get_done_value(title, team, done_msg)
            return '-'

        data = [
            (team,) +
            tuple(format_count(t, team) for t in all_titles) + (
                fail_counts.get(team, 0),
                unreviewed_counts.get(team, 0),
                sum(v.get(team, 0) for v in team_counts.values()),
                assignments.get(team, '')
            )
            for team in sorted(interesting_teams,
                               key=lambda x: x.lower())
        ]

        # How many projects needed changes of this type?
        needed_counts = {
            title: 0
            for title in all_titles
        }
        # How many projects have completed the changes of this type?
        done_counts = {
            title: 0
            for title in all_titles
        }
        for row in data:
            for i, t in enumerate(all_titles, 1):
                if row[i] == '-':
                    # ignore this row for this column
                    continue
                needed_counts[t] += 1
                if row[i] == '+':
                    done_counts[t] += 1

        summary_lines = {}
        for title, count in done_counts.items():
            summary_lines[title] = '{:3}/{:3}'.format(
                count, needed_counts[title])

        total_fail = sum(fail_counts.values())
        total_unreviewed = sum(unreviewed_counts.values())
        total_all = sum(sum(v.values()) for v in team_counts.values())

        data.append(
            ('',) +
            tuple(summary_lines.get(t, '') for t in all_titles) + (
                total_fail,
                total_unreviewed,
                total_all,
                '')
        )

        if parsed_args.only_open:
            data = [
                row
                for row in data
                if ''.join(row[1:4]).strip('+-')
            ]

        return (columns, data)
