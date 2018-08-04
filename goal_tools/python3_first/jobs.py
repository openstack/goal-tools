#!/usr/bin/env python3

# Show the project settings for the repository that should be moved
# into the tree at a given branch.

import configparser
import copy
import glob
import io
import logging
import os.path
import re

from goal_tools import governance
from goal_tools.python3_first import projectconfig_ruamellib

from cliff import command
from ruamel.yaml import comments

LOG = logging.getLogger(__name__)

# Items we know we need to keep in project-config.
KEEP = set([
    'translation-jobs',
    'translation-jobs-queens',
    'translation-jobs-rocky',

    'periodic-jobs-with-oslo-master',

    'api-ref-jobs',

    'release-openstack-server',

    'publish-to-pypi',
    'publish-to-pypi-python3',
    'publish-to-pypi-quietly',
    'publish-to-pypi-horizon',
    'publish-to-pypi-neutron',

    'noop-jobs',
])

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


def find_templates_only_on_master(project, zuul_templates, zuul_jobs):
    templates = project.get('templates', [])

    needs_to_stay = set()

    for template_name in templates:
        if template_name in needs_to_stay:
            continue

        LOG.debug('looking at template %r', template_name)

        jobs_only_on_master = set()
        try:
            template_settings = zuul_templates[template_name]
        except KeyError:
            LOG.debug('did not find template definition for %r',
                      template_name)
            continue

        for queue_name in template_settings.keys():

            queue = template_settings[queue_name]
            if not isinstance(queue, dict):
                continue

            for job in queue.get('jobs', []):
                if isinstance(job, str):
                    job_name = job
                    try:
                        job_params = zuul_jobs[job_name]
                    except KeyError:
                        LOG.debug('could not find job definition for %r',
                                  job_name)
                        continue
                else:
                    job_name = list(job.keys())[0]
                    job_params = list(job.values())[0]
                LOG.debug('looking at job %s', job_name)
                branches = list(branches_for_job(job_params))
                LOG.debug('branches: %r', branches)
                if branches == ['master']:
                    LOG.debug('ONLY ON MASTER')
                    jobs_only_on_master.add(job_name)

        if jobs_only_on_master:
            needs_to_stay.add(template_name)

    return needs_to_stay


def find_templates_to_extract(project, zuul_templates, zuul_jobs):
    templates = project.get('templates', [])

    # Initialize the set of templates we need to keep in
    # project-config with some things we know about, then add any with
    # jobs only on the master branch.
    needs_to_stay = KEEP.union(find_templates_only_on_master(
        project, zuul_templates, zuul_jobs))

    to_keep = [
        t
        for t in templates
        if t not in needs_to_stay
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
            '--openstack-zuul-jobs-dir',
            default='../openstack-zuul-jobs',
            help='the location of the openstack-zuul-jobs repo',
        )
        parser.add_argument(
            'repo',
            help='the repository name',
        )
        parser.add_argument(
            'branch',
            nargs='*',
            default=BRANCHES,
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

        zuul_templates_filename = os.path.join(
            parsed_args.openstack_zuul_jobs_dir,
            'zuul.d',
            'project-templates.yaml',
        )
        LOG.debug('loading project templates from %s', zuul_templates_filename)
        with open(zuul_templates_filename, 'r', encoding='utf-8') as f:
            zuul_templates_raw = yaml.load(f)
        zuul_templates = {
            pt['project-template']['name']: pt['project-template']
            for pt in zuul_templates_raw
            if 'project-template' in pt
        }

        zuul_jobs_filename = os.path.join(
            parsed_args.openstack_zuul_jobs_dir,
            'zuul.d',
            'jobs.yaml',
        )
        LOG.debug('loading jobs from %s', zuul_jobs_filename)
        with open(zuul_jobs_filename, 'r', encoding='utf-8') as f:
            zuul_jobs_raw = yaml.load(f)
        zuul_jobs = {
            job['job']['name']: job['job']
            for job in zuul_jobs_raw
            if 'job' in job
        }

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
        find_templates_to_extract(entry['project'], zuul_templates, zuul_jobs)

        for branch in parsed_args.branch:
            to_update = copy.deepcopy(entry)
            filter_jobs_on_branch(to_update['project'], parsed_args.branch)

            # Remove the 'name' value in case we can copy the results
            # directly into a new file.
            if 'name' in to_update['project']:
                del to_update['project']['name']

            print()
            print('# {} @ {}'.format(parsed_args.repo, branch))
            yaml.dump([to_update], self.app.stdout)


def find_project_settings_in_repo(repo_dir):
    yaml = projectconfig_ruamellib.YAML()
    candidate_bases = [
        '.zuul.yaml',
        'zuul.yaml',
        '.zuul.d/*.yaml',
        'zuul.d/*.yaml',
    ]
    for base in candidate_bases:
        pattern = os.path.join(repo_dir, base)
        for candidate in glob.glob(pattern):
            LOG.debug('looking for zuul config in %s',
                      candidate)
            with open(candidate, 'r', encoding='utf-8') as f:
                settings = yaml.load(f)
            for block in settings:
                if 'project' in block:
                    LOG.debug('using zuul config from %s',
                              candidate)
                    return (candidate, block, settings)
    LOG.debug('did not find in-tree project settings')
    return (None, {}, [])


def merge_pipeline(name, in_tree, updates):
    LOG.debug('merging pipeline %s', name)
    # Copy the settings other than the jobs.
    for key in updates.keys():
        if key == 'jobs':
            continue
        if key not in in_tree:
            # Data structures created by the YAML library use a
            # CommentedMap object, which has an insert() method that
            # lets us add something to the map in a particular place
            # in order. To keep the file easy to read, we insert keys
            # other than 'jobs' at the start of the map.
            LOG.debug('copying new setting %s', key)
            in_tree.insert(0, key, updates[key])
        else:
            LOG.debug('updating existing setting %s', key)
            in_tree[key] = updates[key]
    # Merge the job list
    job_names = set()
    jobs = in_tree.get('jobs', [])
    for job in jobs:
        if isinstance(job, dict):
            job_names.add(list(job.keys())[0])
        else:
            job_names.add(job)
    for job in updates.get('jobs', []):
        if isinstance(job, dict):
            job_name = list(job.keys())[0]
            job_info = list(job.values())[0]
        else:
            job_name = job
            job_info = None
        if job_name in job_names:
            LOG.debug('duplicate job found: %s - %s',
                      job_name, job_info)
            continue
        job_names.add(job_name)
        if job_info is None:
            jobs.append(job_name)
        else:
            jobs.append(job)
    if jobs and 'jobs' not in in_tree:
        in_tree['jobs'] = jobs
    return in_tree


def merge_project_settings(in_tree, updates):
    itp = in_tree.setdefault('project', comments.CommentedMap())
    up = updates.get('project', comments.CommentedMap())
    LOG.debug('merging templates')
    templates = itp.get('templates', [])
    for t in up.get('templates', []):
        if t not in templates:
            LOG.debug('  adding %s', t)
            templates.append(t)
    if templates and 'templates' not in itp:
        LOG.debug('  saving updates')
        itp.insert(0, 'templates', templates)
    for pipeline in up.keys():
        if pipeline == 'templates':
            continue
        new_data = merge_pipeline(
            pipeline,
            itp.get(pipeline, {}),
            up.get(pipeline, {}),
        )
        if new_data and pipeline not in itp:
            LOG.debug('  saving %s', pipeline)
            itp[pipeline] = new_data
    return in_tree


class JobsUpdate(command.Command):
    "update the in-tree project settings"

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--project-config-dir',
            default='../project-config',
            help='the location of the project-config repo',
        )
        parser.add_argument(
            '--openstack-zuul-jobs-dir',
            default='../openstack-zuul-jobs',
            help='the location of the openstack-zuul-jobs repo',
        )
        parser.add_argument(
            '--default-zuul-file',
            default='.zuul.yaml',
            help='the default file to create when one does not exist',
        )
        parser.add_argument(
            'repo_dir',
            help='the repository location',
        )
        return parser

    def take_action(self, parsed_args):
        LOG.debug('determining repository name from .gitreview')
        gitreview_filename = os.path.join(parsed_args.repo_dir, '.gitreview')
        cp = configparser.ConfigParser()
        cp.read(gitreview_filename)
        gerrit = cp['gerrit']
        repo = gerrit['project']
        if repo.endswith('.git'):
            repo = repo[:-4]
        branch = gerrit.get('defaultbranch', 'master')
        LOG.info('working on %s @ %s', repo, branch)

        in_repo = find_project_settings_in_repo(parsed_args.repo_dir)
        in_tree_file, in_tree_project, in_tree_settings = in_repo

        yaml = projectconfig_ruamellib.YAML()

        project_filename = os.path.join(
            parsed_args.project_config_dir,
            'zuul.d',
            'projects.yaml',
        )
        LOG.debug('loading project settings from %s', project_filename)
        with open(project_filename, 'r', encoding='utf-8') as f:
            project_settings = yaml.load(f)

        zuul_templates_filename = os.path.join(
            parsed_args.openstack_zuul_jobs_dir,
            'zuul.d',
            'project-templates.yaml',
        )
        LOG.debug('loading project templates from %s', zuul_templates_filename)
        with open(zuul_templates_filename, 'r', encoding='utf-8') as f:
            zuul_templates_raw = yaml.load(f)
        zuul_templates = {
            pt['project-template']['name']: pt['project-template']
            for pt in zuul_templates_raw
            if 'project-template' in pt
        }

        zuul_jobs_filename = os.path.join(
            parsed_args.openstack_zuul_jobs_dir,
            'zuul.d',
            'jobs.yaml',
        )
        LOG.debug('loading jobs from %s', zuul_jobs_filename)
        with open(zuul_jobs_filename, 'r', encoding='utf-8') as f:
            zuul_jobs_raw = yaml.load(f)
        zuul_jobs = {
            job['job']['name']: job['job']
            for job in zuul_jobs_raw
            if 'job' in job
        }

        LOG.debug('looking for settings for %s', repo)
        for entry in project_settings:
            if 'project' not in entry:
                continue
            if entry['project'].get('name') == repo:
                break
        else:
            raise ValueError('Could not find {} in {}'.format(
                repo, project_filename))

        # Remove the items that need to stay in project-config.
        find_templates_to_extract(entry['project'], zuul_templates, zuul_jobs)

        filter_jobs_on_branch(entry['project'], branch)

        # Remove the 'name' value in case we can copy the results
        # directly into a new file.
        if 'name' in entry['project']:
            del entry['project']['name']

        merge_project_settings(
            in_tree_project,
            entry,
        )

        if not in_tree_project.get('project'):
            LOG.info('no settings to write')
            return 1

        if not in_tree_settings:
            in_tree_settings.append(in_tree_project)

        LOG.info('# {} @ {}'.format(repo, branch))
        yaml.dump(in_tree_settings, self.app.stdout)

        if not in_tree_file:
            in_tree_file = os.path.join(
                parsed_args.repo_dir,
                parsed_args.default_zuul_file,
            )
            out_dir = os.path.dirname(in_tree_file)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            LOG.info('creating %s', in_tree_file)
        else:
            LOG.info('updating %s', in_tree_file)
        with open(in_tree_file, 'w', encoding='utf-8') as f:
            yaml.dump(in_tree_settings, f)


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


def find_templates_to_retain(project, zuul_templates, zuul_jobs):
    # Initialize the set of templates we need to keep in
    # project-config with some things we know about, then add any with
    # jobs only on the master branch.
    needs_to_stay = KEEP.union(find_templates_only_on_master(
        project, zuul_templates, zuul_jobs))
    templates = project.get('templates', [])
    to_keep = [
        t
        for t in templates
        if t in needs_to_stay
    ]
    if to_keep:
        project['templates'] = to_keep
    elif 'templates' in project:
        del project['templates']


def need_to_keep(entry):
    project = entry.get('project', {})
    if project.get('templates'):
        return True
    for key, value in project.items():
        if not isinstance(value, dict):
            continue
        if 'jobs' in value:
            return True
    return False


class JobsRetain(command.Command):
    "reduce the project settings for a team's repos in project-config"

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--project-list',
            default=governance.PROJECTS_LIST,
            help='URL for projects.yaml',
        )
        parser.add_argument(
            '--project-config-dir',
            default='../project-config',
            help='the location of the project-config repo',
        )
        parser.add_argument(
            '--openstack-zuul-jobs-dir',
            default='../openstack-zuul-jobs',
            help='the location of the openstack-zuul-jobs repo',
        )
        parser.add_argument(
            '--dry-run', '-n',
            default=False,
            action='store_true',
            help='show the work but do not change anything',
        )
        parser.add_argument(
            'team',
            help='the team name',
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

        zuul_templates_filename = os.path.join(
            parsed_args.openstack_zuul_jobs_dir,
            'zuul.d',
            'project-templates.yaml',
        )
        LOG.debug('loading project templates from %s', zuul_templates_filename)
        with open(zuul_templates_filename, 'r', encoding='utf-8') as f:
            zuul_templates_raw = yaml.load(f)
        zuul_templates = {
            pt['project-template']['name']: pt['project-template']
            for pt in zuul_templates_raw
            if 'project-template' in pt
        }

        zuul_jobs_filename = os.path.join(
            parsed_args.openstack_zuul_jobs_dir,
            'zuul.d',
            'jobs.yaml',
        )
        LOG.debug('loading jobs from %s', zuul_jobs_filename)
        with open(zuul_jobs_filename, 'r', encoding='utf-8') as f:
            zuul_jobs_raw = yaml.load(f)
        zuul_jobs = {
            job['job']['name']: job['job']
            for job in zuul_jobs_raw
            if 'job' in job
        }

        gov_dat = governance.Governance(url=parsed_args.project_list)
        for repo in gov_dat.get_repos_for_team(parsed_args.team):
            LOG.debug('looking for settings for %s', repo)
            for entry in project_settings:
                if 'project' not in entry:
                    continue
                if entry['project'].get('name') == repo:
                    break
            else:
                LOG.warning('Could not find {} in {}'.format(
                    repo, project_filename))
                continue

            find_templates_to_retain(
                entry['project'],
                zuul_templates,
                zuul_jobs,
            )

            find_jobs_to_retain(entry['project'])

            print()
            if need_to_keep(entry):
                yaml.dump([entry], self.app.stdout)
            else:
                print('# No settings to retain for {}.\n'.format(repo))

        if parsed_args.dry_run:
            LOG.debug('not writing project settings to %s',
                      project_filename)
            return 0

        LOG.debug('writing project settings to %s', project_filename)
        # The YAML representation removes existing blank lines between
        # the "- project:" blocks. This code reformats the YAML output
        # to restore the blank lines and ensure that the file always
        # ends in a newline.
        buffer = io.StringIO()
        yaml.dump(project_settings, buffer)
        body = buffer.getvalue()
        parts = body.split('- project:')
        body = '\n\n- project:'.join(p.rstrip() for p in parts) + '\n'
        with open(project_filename, 'w', encoding='utf-8') as f:
            f.write(body)


def update_docs_job(project):
    "replace old documentation job with new version"
    try:
        proj_data = project.get('project', {})
        templates = proj_data.get('templates', [])
        LOG.info('found templates: %s', templates)
        idx = templates.index('publish-openstack-sphinx-docs')
        templates[idx] = 'publish-openstack-docs-pti'
        return True
    except ValueError:
        return False


class JobsSwitchDocs(command.Command):
    "update the in-tree project settings for the new docs PTI"

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--default-zuul-file',
            default='.zuul.yaml',
            help='the default file to create when one does not exist',
        )
        parser.add_argument(
            'repo_dir',
            help='the repository location',
        )
        return parser

    def take_action(self, parsed_args):
        LOG.debug('determining repository name from .gitreview')
        gitreview_filename = os.path.join(parsed_args.repo_dir, '.gitreview')
        cp = configparser.ConfigParser()
        cp.read(gitreview_filename)
        gerrit = cp['gerrit']
        repo = gerrit['project']
        if repo.endswith('.git'):
            repo = repo[:-4]
        LOG.info('working on %s', repo)

        in_repo = find_project_settings_in_repo(parsed_args.repo_dir)
        in_tree_file, in_tree_project, in_tree_settings = in_repo
        if not in_tree_file:
            raise RuntimeError('Could not find project settings in {}'.format(
                parsed_args.repo_dir))

        changed = update_docs_job(in_tree_project)

        if not changed:
            LOG.info('No updates needed for %s', repo)
            return 1

        LOG.info('# {} switch docs jobs'.format(repo))
        yaml = projectconfig_ruamellib.YAML()
        yaml.dump(in_tree_settings, self.app.stdout)
        LOG.info('updating %s', in_tree_file)
        with open(in_tree_file, 'w', encoding='utf-8') as f:
            yaml.dump(in_tree_settings, f)


class JobsSwitchPackaging(command.Command):
    "update the project-config settings for the new packaging job"

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--project-config-dir',
            default='../project-config',
            help='the location of the project-config repo',
        )
        parser.add_argument(
            '--project-list',
            default=governance.PROJECTS_LIST,
            help='URL for projects.yaml',
        )
        return parser

    CANDIDATES = [
        'publish-to-pypi',
        'publish-to-pypi-horizon',
        'publish-to-pypi-neutron',
        'release-openstack-server',
    ]

    def take_action(self, parsed_args):
        yaml = projectconfig_ruamellib.YAML()

        gov_dat = governance.Governance(url=parsed_args.project_list)
        all_repos = set(gov_dat.get_repos())
        if not all_repos:
            raise ValueError('found no governed repositories')

        project_filename = os.path.join(
            parsed_args.project_config_dir,
            'zuul.d',
            'projects.yaml',
        )
        LOG.debug('loading project settings from %s', project_filename)
        with open(project_filename, 'r', encoding='utf-8') as f:
            project_settings = yaml.load(f)

        for entry in project_settings:
            if 'project' not in entry:
                continue
            project = entry['project']
            if project['name'] not in all_repos:
                continue
            if 'templates' not in project:
                continue
            templates = project['templates']
            for candidate in self.CANDIDATES:
                try:
                    idx = templates.index(candidate)
                except (ValueError, IndexError):
                    pass
                else:
                    LOG.info('updating %s', project['name'])
                    templates[idx] = 'publish-to-pypi-python3'

        with open(project_filename, 'w', encoding='utf-8') as f:
            yaml.dump(project_settings, f)
