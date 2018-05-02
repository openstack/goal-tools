# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from goal_tools.tests import base

from goal_tools import governance

import yaml


_team_data_yaml = """
Release Management:
  ptl:
    name: Doug Hellmann
    irc: dhellmann
    email: doug@doughellmann.com
  irc-channel: openstack-release
  mission: >
    Coordinating the release of OpenStack deliverables, by defining the
    overall development cycle, release models, publication processes,
    versioning rules and tools, then enabling project teams to produce
    their own releases.
  url: https://wiki.openstack.org/wiki/Release_Management
  tags:
    - team:diverse-affiliation
  deliverables:
    release-schedule-generator:
      repos:
        - openstack/release-schedule-generator
    release-test:
      repos:
        - openstack/release-test
    release-tools:
      repos:
        - openstack-infra/release-tools
    releases:
      repos:
        - openstack/releases
    reno:
      repos:
        - openstack/reno
      docs:
        contributor: https://docs.openstack.org/developer/reno/
    specs-cookiecutter:
      repos:
        - openstack-dev/specs-cookiecutter
"""

TEAM_DATA = governance._organize_team_data(
    yaml.load(_team_data_yaml),
    {'Technical Committee': [{'repo': 'openstack/governance'}]},
)


class TestGetRepoOwner(base.TestCase):

    def test_repo_exists(self):
        owner = governance.get_repo_owner(
            TEAM_DATA,
            'openstack/releases',
        )
        self.assertEqual('Release Management', owner)

    def test_no_such_repo(self):
        self.assertIsNone(
            governance.get_repo_owner(
                TEAM_DATA,
                'openstack/no-such-repo',
            ),
        )
