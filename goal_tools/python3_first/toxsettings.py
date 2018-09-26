#!/usr/bin/env python3

import configparser
import logging
import os.path
import subprocess

from goal_tools import governance

from cliff import lister

LOG = logging.getLogger(__name__)

ENVS = [
    'bindep',
    'cover',
    'docs',
    'linters',
    'lower-constraints',
    'pep8',
    'releasenotes',
    'venv'
]


def get_tox_config(repo_dir):
    LOG.debug('getting tox settings in %s', repo_dir)
    try:
        result = subprocess.run(
            ['tox', '--showconfig'],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=repo_dir,
        )
    except subprocess.CalledProcessError:
        LOG.info('unable to fetch tox settings for %s', repo_dir)
        return None
    text = result.stdout.decode('utf-8')
    # The preamble of the output is not INI format,
    # so we skip over it by looking for a double blank line.
    return text.partition('\n\n')[-1]


def check_one(repo_base_dir, repo):
    repo_dir = os.path.join(os.path.expanduser(repo_base_dir), repo)
    if not os.path.exists(os.path.join(repo_dir, 'tox.ini')):
        LOG.info('skipping %s', repo)
        return
    LOG.info('scanning %s', repo)
    config = get_tox_config(repo_dir)
    LOG.debug(config)
    if config is None:
        return
    parser = configparser.ConfigParser()
    parser.read_string(config, repo)
    for env in ENVS:
        section = 'testenv:{}'.format(env)
        if not parser.has_section(section):
            LOG.debug('%s has no section %s', repo, section)
            continue
        if not parser.has_option(section, 'basepython'):
            yield (section, 'not set')
            continue
        value = parser.get(section, 'basepython')
        if 'python3' not in value:
            yield (section, 'set to {!r}'.format(value))
            continue
        yield (section, 'OK')


class ToxMissingPy3(lister.Lister):
    "list the tox environments missing python3 settings"

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
        columns = ('Team', 'Repo', 'Env', 'Status')

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
            (team, r, env, status)
            for team, r in teams_and_repos
            for env, status in check_one(parsed_args.repo_base_dir, r)
            if team != 'Infrastructure'
        ]

        if parsed_args.errors_only:
            data = [
                r
                for r in data
                if r[-1] != 'OK'
            ]

        return (columns, data)
