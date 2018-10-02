#!/usr/bin/env python3

import configparser
import logging
import os.path

from cliff import lister

from goal_tools import governance

LOG = logging.getLogger(__name__)


def get_setup_config(repo_dir):
    LOG.debug('getting settings in %s', repo_dir)
    input_name = os.path.join(repo_dir, 'setup.cfg')
    parser = configparser.ConfigParser()
    parser.read([input_name])
    return parser


def check_one(repo_base_dir, repo):
    # Specs repositories aren't packaged
    if repo.endswith('-specs'):
        return 'not needed'
    # Charm repositories don't need to build wheels
    repo_base = repo.partition('/')[-1]
    if repo_base.startswith('charm-'):
        return 'not needed'
    # Puppet repos don't build wheels
    if repo_base.startswith('puppet-'):
        return 'not needed'
    # xstatic repos don't need wheels
    if repo_base.startswith('xstatic-'):
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
