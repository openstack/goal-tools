#!/usr/bin/env python3

import configparser
import logging
import os
import os.path
import shutil
import subprocess

from cliff import command
from cliff import lister

from goal_tools import governance

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


start_dir = os.getcwd()
tools_dir = os.path.join(start_dir, 'tools')


def clone_repo(workdir, repo):
    LOG.info('cloning %s', repo)
    repo_dir = os.path.join(workdir, repo)
    if os.path.exists(repo_dir):
        raise RuntimeError('Found another copy of {} at {}'.format(
            repo, repo_dir))
    subprocess.run(
        [os.path.join(tools_dir, 'clone_repo.sh'),
         '--workspace', workdir,
         repo],
        check=True,
    )


def git(repo_dir, *args):
    subprocess.run(
        ['git'] + list(args),
        check=True,
        cwd=repo_dir,
    )


COMMIT_MESSAGE = '''\
fix tox python3 overrides

We want to default to running all tox environments under python 3, so
set the basepython value in each environment.

We do not want to specify a minor version number, because we do not
want to have to update the file every time we upgrade python.

We do not want to set the override once in testenv, because that
breaks the more specific versions used in default environments like
py35 and py36.

Signed-off-by: Doug Hellmann <doug@doughellmann.com>
'''


def fix_one(workdir, repo, bad_envs):
    LOG.info('processing %s', repo)
    repo_dir = os.path.join(workdir, repo)
    git(repo_dir, 'checkout', 'master')
    git(repo_dir, 'checkout', '-b', 'python3-first-tox')
    tox_file = os.path.join(repo_dir, 'tox.ini')
    with open(tox_file, 'r', encoding='utf-8') as f:
        tox_contents = f.read()
    for env in bad_envs:
        env_header = '[{}]\n'.format(env)
        LOG.info('updating %r', env_header.rstrip())
        tox_contents = tox_contents.replace(
            env_header,
            env_header + 'basepython = python3\n',
        )
    with open(tox_file, 'w', encoding='utf-8') as f:
        f.write(tox_contents)
    git(repo_dir, 'diff')
    git(repo_dir, 'add', 'tox.ini')
    git(repo_dir, 'review', '-s')
    git(repo_dir, 'commit', '-m', COMMIT_MESSAGE)
    git(repo_dir, 'show')


class ToxFixMissingPy3(command.Command):
    "fix the tox environments missing python3 settings"

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

            team_dir = os.path.join(workdir, team).replace(' ', '-')
            if not os.path.exists(team_dir):
                LOG.info('creating %s', team_dir)
                os.mkdir(team_dir)

            tracking_file = os.path.join(team_dir, 'master')

            clone_repo(team_dir, r)

            bad_envs = [
                env
                for env, status in check_one(team_dir, r)
                if status != 'OK'
            ]

            if not bad_envs:
                LOG.info('nothing to change for %s', r)
                shutil.rmtree(os.path.join(team_dir, r))
                continue

            fix_one(team_dir, r, bad_envs)

            LOG.info('adding %s to %s', r, tracking_file)
            with open(tracking_file, 'a', encoding='utf-8') as f:
                f.write('{}\n'.format(r))
