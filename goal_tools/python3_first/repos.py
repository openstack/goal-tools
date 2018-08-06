#!/usr/bin/env python3

import logging
import os.path
import subprocess
import textwrap

from goal_tools import governance

from cliff import command
import jinja2

LOG = logging.getLogger(__name__)

_TOOLS_DIR = os.path.realpath(
    os.path.join(
        os.path.basename(__file__),
        '..',
        'tools',
    )
)


class ReposClone(command.Command):
    "clone the repositories for a team"

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--project-list',
            default=governance.PROJECTS_LIST,
            help='URL for projects.yaml',
        )
        parser.add_argument(
            'workdir',
            help='directory where the cloned repos should go',
        )
        parser.add_argument(
            'team',
            help='the team name',
        )
        return parser

    def take_action(self, parsed_args):
        clone_script = os.path.join(_TOOLS_DIR, 'clone_repo.sh')
        if not os.path.exists(parsed_args.workdir):
            LOG.info('creating working directory %s', parsed_args.workdir)
            os.makedirs(parsed_args.workdir)
        gov_dat = governance.Governance(url=parsed_args.project_list)
        try:
            for repo in gov_dat.get_repos_for_team(parsed_args.team):
                if os.path.exists(os.path.join(parsed_args.workdir, repo)):
                    LOG.info('\n%s exists, skipping', repo)
                    continue
                LOG.info('\n%s cloning', repo)
                subprocess.run(
                    [clone_script,
                     '--workspace', parsed_args.workdir,
                     repo],
                    check=True,
                )
        except ValueError as err:
            print(err)
            return 1


class ReposList(command.Command):
    "list the repositories for a team"

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--project-list',
            default=governance.PROJECTS_LIST,
            help='URL for projects.yaml',
        )
        parser.add_argument(
            'team',
            help='the team name',
        )
        return parser

    def take_action(self, parsed_args):
        gov_dat = governance.Governance(url=parsed_args.project_list)
        try:
            for repo in gov_dat.get_repos_for_team(parsed_args.team):
                print(repo)
        except ValueError as err:
            print(err)
            return 1


class MigrationAnnounce(command.Command):
    "email the infra team a list the locked repositories for a team"

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--project-list',
            default=governance.PROJECTS_LIST,
            help='URL for projects.yaml',
        )
        parser.add_argument(
            'team',
            help='the team name',
        )
        return parser

    body_template = textwrap.dedent('''
    The Zuul project settings for the {{team}} repositories
    has begun. Please do not approve any changes to
    openstack-infra/project-config/zuul.d/projects.yaml for
    the following repositories:
    {% for repo in repos %}
    - {{repo}}
    {%- endfor %}
    ''')

    def take_action(self, parsed_args):
        gov_dat = governance.Governance(url=parsed_args.project_list)
        repos = sorted(list(gov_dat.get_repos_for_team(parsed_args.team)))

        template = jinja2.Template(
            source=self.body_template,
            undefined=jinja2.StrictUndefined,
        )
        body = template.render(
            team=parsed_args.team,
            repos=repos,
        )
        print(body)
