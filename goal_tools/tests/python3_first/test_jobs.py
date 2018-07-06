# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from goal_tools.python3_first import jobs
from goal_tools.tests import base


class TestBranchesForJob(base.TestCase):

    def test_none(self):
        params = {}
        self.assertEqual(
            [],
            list(jobs.branches_for_job(params)),
        )

    def test_regex_string(self):
        params = {
            'branches': '^master',
        }
        self.assertEqual(
            ['master'],
            list(jobs.branches_for_job(params)),
        )

    def test_regex_list(self):
        params = {
            'branches': [
                '^master',
                'ocata',
            ]
        }
        self.assertEqual(
            ['master', 'stable/ocata'],
            list(jobs.branches_for_job(params)),
        )


class TestFilterJobsOnBranch(base.TestCase):

    def test_no_jobs(self):
        project = {
            'templates': [
                'integrated-gate',
                'integrated-gate-py35',
                'publish-openstack-sphinx-docs',
            ],
        }
        expected = {
            'templates': [
                'integrated-gate',
                'integrated-gate-py35',
                'publish-openstack-sphinx-docs',
            ],
        }
        jobs.filter_jobs_on_branch(project, 'master')
        self.assertEqual(expected, project)

    def test_no_match(self):
        project = {
            'check': {
                'jobs': [
                    {
                        'legacy-devstack-dsvm-updown': {
                            'branches': 'stable',
                        }
                    },
                ],
            },
        }
        expected = {
        }
        jobs.filter_jobs_on_branch(project, 'master')
        self.assertEqual(expected, project)

    def test_no_regex(self):
        project = {
            'check': {
                'jobs': [
                    'openstack-tox-bashate',
                ],
            },
        }
        expected = {
            'check': {
                'jobs': [
                    'openstack-tox-bashate',
                ],
            },
        }
        jobs.filter_jobs_on_branch(project, 'master')
        self.assertEqual(expected['check']['jobs'], project['check']['jobs'])

    def test_stable_match(self):
        project = {
            'check': {
                'jobs': [
                    {
                        'legacy-devstack-dsvm-updown': {
                            'branches': '^stable',
                        }
                    },
                ],
            },
        }
        expected = {
            'check': {
                'jobs': [
                    'legacy-devstack-dsvm-updown',
                ],
            },
        }
        jobs.filter_jobs_on_branch(project, 'stable/ocata')
        self.assertEqual(expected['check']['jobs'], project['check']['jobs'])

    def test_master(self):
        # Because legacy-devstack-dsvm-updown *only* matches the
        # master branch the settings to include it need to stay in
        # project-config.
        project = {
            'check': {
                'jobs': [
                    'openstack-tox-bashate',
                    {
                        'legacy-devstack-dsvm-updown': {
                            'branches': '^(?!stable)',
                        }
                    },
                ],
            },
        }
        expected = {
            'check': {
                'jobs': [
                    'openstack-tox-bashate',
                ],
            },
        }
        jobs.filter_jobs_on_branch(project, 'master')
        self.assertEqual(expected['check']['jobs'], project['check']['jobs'])


class TestFindJobsToRetain(base.TestCase):

    def test_no_jobs(self):
        project = {
            'templates': [
                'integrated-gate',
                'integrated-gate-py35',
                'publish-openstack-sphinx-docs',
            ],
            'check': {
                'jobs': [],
            },
        }
        expected = {
            'templates': [
                'integrated-gate',
                'integrated-gate-py35',
                'publish-openstack-sphinx-docs',
            ],
        }
        jobs.find_jobs_to_retain(project)
        self.assertEqual(expected, project)

    def test_no_match(self):
        project = {
            'check': {
                'jobs': [
                    'openstack-tox-bashate',
                    {
                        'legacy-devstack-dsvm-updown': {
                            'branches': '^stable',
                        }
                    },
                ],
            },
        }
        expected = {
        }
        jobs.find_jobs_to_retain(project)
        self.assertEqual(expected, project)

    def test_stable_match(self):
        project = {
            'check': {
                'jobs': [
                    'openstack-tox-bashate',
                    {
                        'legacy-devstack-dsvm-updown': {
                            'branches': '^stable',
                        }
                    },
                ],
            },
        }
        expected = {
        }
        jobs.find_jobs_to_retain(project)
        self.assertEqual(expected, project)

    def test_master(self):
        # Because legacy-devstack-dsvm-updown *only* matches the
        # master branch the settings to include it need to stay in
        # project-config.
        project = {
            'check': {
                'jobs': [
                    'openstack-tox-bashate',
                    {
                        'legacy-devstack-dsvm-updown': {
                            'branches': '^(?!stable)',
                        }
                    },
                ],
            },
        }
        expected = {
            'check': {
                'jobs': [
                    {
                        'legacy-devstack-dsvm-updown': {
                            'branches': '^(?!stable)',
                        }
                    },
                ],
            },
        }
        jobs.find_jobs_to_retain(project)
        self.assertEqual(expected['check']['jobs'], project['check']['jobs'])


class TestJobsExtractTemplates(base.TestCase):

    def test_no_templates(self):
        project = {
        }
        expected = {
        }
        jobs.find_templates_to_extract(project, {}, {})
        self.assertEqual(expected, project)

    def test_no_templates_remain(self):
        project = {
            'templates': [
                'translation-jobs',
            ],
        }
        expected = {
        }
        jobs.find_templates_to_extract(project, {}, {})
        self.assertEqual(expected, project)

    def test_translation_jobs(self):
        project = {
            'templates': [
                'translation-jobs',
                'integrated-gate',
                'integrated-gate-py35',
                'publish-openstack-sphinx-docs',
            ],
        }
        expected = {
            'templates': [
                'integrated-gate',
                'integrated-gate-py35',
                'publish-openstack-sphinx-docs',
            ],
        }
        jobs.find_templates_to_extract(project, {}, {})
        self.assertEqual(expected, project)


class TestJobsRetainTemplates(base.TestCase):

    def test_no_templates(self):
        project = {
        }
        expected = {
        }
        jobs.find_templates_to_retain(project, {}, {})
        self.assertEqual(expected, project)

    def test_no_templates_remain(self):
        project = {
            'templates': [
                'translation-jobs',
            ],
        }
        expected = {
            'templates': [
                'translation-jobs',
            ],
        }
        jobs.find_templates_to_retain(project, {}, {})
        self.assertEqual(expected, project)

    def test_translation_jobs(self):
        project = {
            'templates': [
                'translation-jobs',
                'integrated-gate',
                'integrated-gate-py35',
                'publish-openstack-sphinx-docs',
            ],
        }
        expected = {
            'templates': [
                'translation-jobs',
            ],
        }
        jobs.find_templates_to_retain(project, {}, {})
        self.assertEqual(expected, project)


class TestFindTemplatesOnlyOnMaster(base.TestCase):

    def test_no_templates(self):
        project = {
        }
        zuul_templates = {}
        zuul_jobs = {}
        expected = set()
        actual = jobs.find_templates_only_on_master(
            project, zuul_templates, zuul_jobs)
        self.assertEqual(expected, actual)

    def test_template_not_in_zuul_data(self):
        project = {
            'templates': [
                'undefined-template',
            ],
        }
        zuul_templates = {}
        zuul_jobs = {}
        expected = set()
        actual = jobs.find_templates_only_on_master(
            project, zuul_templates, zuul_jobs)
        self.assertEqual(expected, actual)

    def test_template_without_branches(self):
        project = {
            'templates': [
                'unbranched-template',
            ],
        }
        zuul_templates = {
            'unbranched-template': {
                'check': ['job1'],
            }
        }
        zuul_jobs = {}
        expected = set()
        actual = jobs.find_templates_only_on_master(
            project, zuul_templates, zuul_jobs)
        self.assertEqual(expected, actual)

    def test_template_other_branch(self):
        project = {
            'templates': [
                'branched-template',
            ],
        }
        zuul_templates = {
            'branched-template': {
                'check': {
                    'jobs': [
                        {'job1': {'branches': 'stable/.*'}},
                    ],
                },
            },
        }
        zuul_jobs = {}
        expected = set()
        actual = jobs.find_templates_only_on_master(
            project, zuul_templates, zuul_jobs)
        self.assertEqual(expected, actual)

    def test_template_master_branch(self):
        project = {
            'templates': [
                'master-template',
            ],
        }
        zuul_templates = {
            'master-template': {
                'check': {
                    'jobs': [
                        {'job1': {'branches': 'master'}},
                    ],
                },
            },
        }
        zuul_jobs = {}
        expected = set(['master-template'])
        actual = jobs.find_templates_only_on_master(
            project, zuul_templates, zuul_jobs)
        self.assertEqual(expected, actual)

    def test_template_other_branch_in_jobs(self):
        project = {
            'templates': [
                'branched-template',
            ],
        }
        zuul_templates = {
            'branched-template': {
                'check': {
                    'jobs': [
                        'job1',
                    ],
                },
            },
        }
        zuul_jobs = {
            'job1': {'branches': 'stable/.*'}
        }
        expected = set()
        actual = jobs.find_templates_only_on_master(
            project, zuul_templates, zuul_jobs)
        self.assertEqual(expected, actual)

    def test_template_master_branch_in_jobs(self):
        project = {
            'templates': [
                'branched-template',
            ],
        }
        zuul_templates = {
            'branched-template': {
                'check': {
                    'jobs': [
                        'job1',
                    ],
                },
            },
        }
        zuul_jobs = {
            'job1': {'branches': 'master'}
        }
        expected = set(['branched-template'])
        actual = jobs.find_templates_only_on_master(
            project, zuul_templates, zuul_jobs)
        self.assertEqual(expected, actual)
