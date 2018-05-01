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

"""Work with the governance repository.
"""

import yaml

from goal_tools import apis

PROJECTS_LIST = "http://git.openstack.org/cgit/openstack/governance/plain/reference/projects.yaml"  # noqa
TC_LIST = "http://git.openstack.org/cgit/openstack/governance/plain/reference/technical-committee-repos.yaml"  # noqa


def get_team_data(url=PROJECTS_LIST, tc_url=TC_LIST):
    """Return the parsed team data from the governance repository.

    :param url: Optional URL to the location of the projects.yaml
        file. Defaults to the most current version in the public git
        repository.

    """
    raw = apis.requester(url)
    team_data = yaml.load(raw.text)

    tc = apis.requester(tc_url)
    tc_data = yaml.load(tc.text)
    team_data['Technical Committee'] = {
        'deliverables': {
            repo['repo'].partition('/')[-1]: {'repos': [repo['repo']]}
            for repo in tc_data['Technical Committee']
        }
    }

    return team_data


def get_repo_owner(team_data, repo_name):
    """Return the name of the team that owns the repository.

    :param team_data: The result of calling :func:`get_team_data`
    :param repo_name: Long name of the repository, such as 'openstack/nova'.

    """
    for team, info in team_data.items():
        for dname, dinfo in info.get('deliverables', {}).items():
            if repo_name in dinfo.get('repos', []):
                return team
    return None
