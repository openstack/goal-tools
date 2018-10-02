#!/usr/bin/env python3

import configparser
import logging
import os.path
import shutil

from cliff import command
from cliff import lister

from goal_tools import gitutils
from goal_tools import governance

LOG = logging.getLogger(__name__)


def get_setup_config(repo_dir):
    LOG.debug('getting settings in %s', repo_dir)
    input_name = os.path.join(repo_dir, 'setup.cfg')
    parser = configparser.ConfigParser()
    parser.read([input_name])
    return parser


def applies_to_repo(repo):
    # Specs repositories aren't packaged
    if repo.endswith('-specs'):
        return False
    # Charm repositories don't need to build wheels
    repo_base = repo.partition('/')[-1]
    if repo_base.startswith('charm-'):
        return False
    # Puppet repos don't build wheels
    if repo_base.startswith('puppet-'):
        return False
    # xstatic repos don't need wheels
    if repo_base.startswith('xstatic-'):
        return False
    if repo_base.endswith('-tempest-plugin'):
        return False
    return True


def check_one(repo_base_dir, repo):
    if not applies_to_repo(repo):
        return 'not needed'
    repo_dir = os.path.join(os.path.expanduser(repo_base_dir), repo)
    if not os.path.exists(os.path.join(repo_dir, 'setup.cfg')):
        LOG.info('skipping %s', repo)
        return 'not needed'
    LOG.info('scanning %s', repo)
    config = get_setup_config(repo_dir)
    if not config.has_option('wheel', 'universal'):
        return 'not set'
    if config['wheel']['universal']:
        return 'OK'
    return 'Disabled'


class WheelMissingUniversal(lister.Lister):
    "list the repos missing the wheel universal setting"

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--repo-base-dir',
            default='~/repos',
            help='base directory where repositories are cloned (%(default)s)',
        )
        parser.add_argument(
            '--project-list',
            default=governance.PROJECTS_LIST,
            help='URL for governance projects.yaml',
        )
        parser.add_argument(
            '--team',
            help='limit search to one team',
        )
        parser.add_argument(
            '--errors-only', '-e',
            default=False,
            action='store_true',
            help='only show mistakes',
        )
        return parser

    def take_action(self, parsed_args):
        columns = ('Team', 'Repo', 'Status')

        gov_dat = governance.Governance(url=parsed_args.project_list)
        if parsed_args.team:
            repos = gov_dat.get_repos_for_team(parsed_args.team)
        else:
            repos = gov_dat.get_repos()

        teams_and_repos = sorted(
            (gov_dat.get_repo_owner(r), r)
            for r in repos
        )

        data = [
            (team, r, check_one(parsed_args.repo_base_dir, r))
            for team, r in teams_and_repos
            if team != 'Infrastructure'
        ]

        if parsed_args.errors_only:
            data = [
                r
                for r in data
                if r[-1] not in ('OK', 'not needed')
            ]

        return (columns, data)


COMMIT_MESSAGE = '''\
build universal wheels

By default setuptools produces a version-specific wheel file so
installation under other versions of Python require extra work at
install time. This change turns on "universal" wheel support, so that
the wheel file will be marked as supporting both Python 2 and 3.

Signed-off-by: Doug Hellmann <doug@doughellmann.com>
'''


def fix_one(workdir, repo):
    LOG.info('processing %s', repo)
    repo_dir = os.path.join(workdir, repo)
    gitutils.git(repo_dir, 'checkout', 'master')
    gitutils.git(repo_dir, 'checkout', '-b', 'python3-first-wheels')
    setup_file = os.path.join(repo_dir, 'setup.cfg')
    with open(setup_file, 'r', encoding='utf-8') as f:
        contents = f.read().rstrip()
    contents = contents + '\n\n[wheel]\nuniversal = 1\n'
    with open(setup_file, 'w', encoding='utf-8') as f:
        f.write(contents)
    gitutils.git(repo_dir, 'diff')
    gitutils.git(repo_dir, 'add', 'setup.cfg')
    gitutils.git(repo_dir, 'review', '-s')
    gitutils.git(repo_dir, 'commit', '-m', COMMIT_MESSAGE)
    gitutils.git(repo_dir, 'show')


class WheelFixMissingUniversal(command.Command):
    "add the flag to build universal wheels"

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--project-list',
            default=governance.PROJECTS_LIST,
            help='URL for governance projects.yaml',
        )
        parser.add_argument(
            'workdir',
            help='working directory for output repositories',
        )
        return parser

    def take_action(self, parsed_args):
        gov_dat = governance.Governance(url=parsed_args.project_list)
        repos = gov_dat.get_repos()

        teams_and_repos = sorted(
            (gov_dat.get_repo_owner(r), r)
            for r in repos
        )

        workdir = os.path.realpath(parsed_args.workdir)

        for team, r in teams_and_repos:
            if team == 'Infrastructure':
                LOG.info('skipping %s', r)
                continue
            if not applies_to_repo(r):
                LOG.info('skipping %s', r)
                continue

            team_dir = os.path.join(workdir, team).replace(' ', '-')
            if not os.path.exists(team_dir):
                LOG.info('creating %s', team_dir)
                os.mkdir(team_dir)

            tracking_file = os.path.join(team_dir, 'master')

            gitutils.clone_repo(team_dir, r)
            status = check_one(team_dir, r)
            if status in ('OK', 'not needed'):
                LOG.info('nothing to change for %s', r)
                shutil.rmtree(os.path.join(team_dir, r))
                continue

            try:
                fix_one(team_dir, r)
            except Exception:
                LOG.exception('failed to update {}'.format(r))
                continue

            LOG.info('adding %s to %s', r, tracking_file)
            with open(tracking_file, 'a', encoding='utf-8') as f:
                f.write('{}\n'.format(r))
