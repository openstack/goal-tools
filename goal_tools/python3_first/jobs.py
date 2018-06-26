#!/usr/bin/env python3

# Show the project settings for the repository that should be moved
# into the tree at a given branch.

import logging
import os.path
import re

from goal_tools.python3_first import projectconfig_ruamellib

from cliff import command

LOG = logging.getLogger(__name__)

# Items to keep in project-config.
KEEP = [
    'system-required',
    'translation-jobs',
]

BRANCHES = [
    'stable/ocata',
    'stable/pike',
    'stable/queens',
    'stable/rocky',
    'master',
]


def branches_for_job(job_params):
    branch_patterns = job_params.get('branches', [])
    if not isinstance(branch_patterns, list):
        branch_patterns = [branch_patterns]
    for pattern in branch_patterns:
        for branch in BRANCHES:
            # LOG.debug('comparing %r with %r', branch, pattern)
            if re.search(pattern, branch):
                yield branch


def filter_jobs_on_branch(project, branch):
    LOG.debug('filtering on %s', branch)
    for queue, value in list(project.items()):
        if not isinstance(value, dict):
            continue
        if queue == 'templates':
            continue
        if 'jobs' not in value:
            continue

        LOG.debug('%s queue', queue)

        keep = []
        for job in value['jobs']:
            if not isinstance(job, dict):
                keep.append(job)
                continue

            job_name = list(job.keys())[0]
            job_params = list(job.values())[0]
            if 'branches' not in job_params:
                keep.append(job)
                continue

            branches = list(branches_for_job(job_params))

            if not branches:
                # The job is not applied to any branches.
                LOG.debug('matches no branches, ignoring')
                continue

            LOG.debug('%s applies to branches: %s',
                      job_name, ', '.join(branches))

            if branch not in branches:
                # The job is not applied to the current branch.
                want = False

            elif len(branches) > 1:
                # The job is applied to multiple branches, so if our
                # branch is in that set we should go ahead and take
                # it.
                want = branch in branches

            else:
                # The job is applied to only 1 branch.  If that branch
                # is the master branch, we need to leave the setting
                # in the project-config file.
                want = branch != 'master'

            if want:
                LOG.debug('%s keeping', job_name)
                del job_params['branches']
                if not job_params:
                    # no parameters left, just add the job name
                    keep.append(job_name)
                else:
                    keep.append(job)
            else:
                LOG.debug('%s ignoring', job_name)

        if keep:
            value['jobs'] = keep
        else:
            del value['jobs']
            if not value:
                del project[queue]


def find_templates_to_extract(project):
    templates = project.get('templates', [])
    to_keep = [
        t
        for t in templates
        if t not in KEEP
    ]
    if to_keep:
        project['templates'] = to_keep
    elif 'templates' in project:
        del project['templates']


class JobsExtract(command.Command):
    "show the project settings to extract for a repository"

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--project-config-dir',
            default='../project-config',
            help='the location of the project-config repo',
        )
        parser.add_argument(
            'repo',
            help='the repository name',
        )
        parser.add_argument(
            'branch',
            help='filter the settings by branch',
        )
        return parser

    def take_action(self, parsed_args):
        yaml = projectconfig_ruamellib.YAML()

        project_filename = os.path.join(
            parsed_args.project_config_dir,
            'zuul.d',
            'projects.yaml',
        )
        LOG.debug('loading project settings from %s', project_filename)
        with open(project_filename, 'r', encoding='utf-8') as f:
            project_settings = yaml.load(f)

        LOG.debug('looking for settings for %s', parsed_args.repo)
        for entry in project_settings:
            if 'project' not in entry:
                continue
            if entry['project'].get('name') == parsed_args.repo:
                break
        else:
            raise ValueError('Could not find {} in {}'.format(
                parsed_args.repo, project_filename))

        # Remove the items that need to stay in project-config.
        find_templates_to_extract(entry['project'])

        # Filter the jobs by branch.
        if parsed_args.branch:
            filter_jobs_on_branch(entry['project'], parsed_args.branch)

        # Remove the 'name' value in case we can copy the results
        # directly into a new file.
        if 'name' in entry['project']:
            del entry['project']['name']

        print()
        yaml.dump([entry], self.app.stdout)


def find_jobs_to_retain(project):
    for queue, value in list(project.items()):
        if not isinstance(value, dict):
            continue
        if queue == 'templates':
            continue
        if 'jobs' not in value:
            continue

        LOG.debug('%s queue', queue)

        keep = []
        for job in value['jobs']:
            if not isinstance(job, dict):
                continue

            job_name = list(job.keys())[0]
            job_params = list(job.values())[0]
            if 'branches' not in job_params:
                continue

            branches = list(branches_for_job(job_params))

            if not branches:
                # The job is not applied to any branches.
                LOG.debug('matches no branches, ignoring')
                continue

            LOG.debug('%s applies to branches: %s',
                      job_name, ', '.join(branches))

            # If the job only applies to the master branch we need to
            # keep it.
            if branches == ['master']:
                LOG.debug('%s keeping', job_name)
                keep.append(job)
            else:
                LOG.debug('%s ignoring', job_name)

        if keep:
            value['jobs'] = keep
        else:
            del value['jobs']
            if not value:
                del project[queue]


def find_templates_to_retain(project):
    # Remove the items that need to move to the project repo.
    templates = project.get('templates', [])
    to_keep = [
        t
        for t in templates
        if t in KEEP
    ]
    if to_keep:
        project['templates'] = to_keep
    elif 'templates' in project:
        del project['templates']


class JobsRetain(command.Command):
    "show the project settings to keep in project-config"

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--project-config-dir',
            default='../project-config',
            help='the location of the project-config repo',
        )
        parser.add_argument(
            'repo',
            help='the repository name',
        )
        return parser

    def take_action(self, parsed_args):
        yaml = projectconfig_ruamellib.YAML()

        project_filename = os.path.join(
            parsed_args.project_config_dir,
            'zuul.d',
            'projects.yaml',
        )
        LOG.debug('loading project settings from %s', project_filename)
        with open(project_filename, 'r', encoding='utf-8') as f:
            project_settings = yaml.load(f)

        LOG.debug('looking for settings for %s', parsed_args.repo)
        for entry in project_settings:
            if 'project' not in entry:
                continue
            if entry['project'].get('name') == parsed_args.repo:
                break
        else:
            raise ValueError('Could not find {} in {}'.format(
                parsed_args.repo, project_filename))

        find_templates_to_retain(entry['project'])

        find_jobs_to_retain(entry['project'])

        print()
        yaml.dump([entry], self.app.stdout)
