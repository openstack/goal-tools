#!/usr/bin/env python3

import logging
import os.path
import subprocess

from goal_tools import governance

from cliff import command

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
