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

import functools

import yaml

from goal_tools import apis

PROJECTS_LIST = "http://git.openstack.org/cgit/openstack/governance/plain/reference/projects.yaml"  # noqa
TC_LIST = "http://git.openstack.org/cgit/openstack/governance/plain/reference/technical-committee-repos.yaml"  # noqa


class Governance:

    def __init__(self, team_data=None, url=PROJECTS_LIST, tc_url=TC_LIST):
        self._url = url
        self._tc_url = tc_url
        if team_data is None:
            team_data = self._fetch_team_data()
        self._team_data = team_data

    def _get_team_data(self):
        "Return the parsed team data from the governance repository."
        raw = apis.requester(self._url)
        team_data = yaml.load(raw.text)
        tc = apis.requester(self._tc_url)
        tc_data = yaml.load(tc.text)
        return self._organize_team_data(team_data, tc_data)

    @staticmethod
    def _organize_team_data(team_data, tc_data):
        team_data['Technical Committee'] = {
            'deliverables': {
                repo['repo'].partition('/')[-1]: {'repos': [repo['repo']]}
                for repo in tc_data['Technical Committee']
            }
        }

        by_repos = {}
        for team, info in team_data.items():
            for dname, dinfo in info.get('deliverables', {}).items():
                for repo in dinfo.get('repos', []):
                    by_repos[repo] = {
                        'team': team,
                        'team_info': info,
                        'deliverable': dname,
                        'deliverable_info': dinfo,
                    }
        team_data['_by_repos'] = by_repos

        return team_data

    @functools.lru_cache()
    def get_repo_owner(self, repo_name):
        "Return the name of the team that owns the repository."
        repo_info = self._team_data['_by_repos'].get(repo_name, {})
        return repo_info.get('team')
