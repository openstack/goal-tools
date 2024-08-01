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

import functools
import logging
import pkgutil

import yaml

LOG = logging.getLogger(__name__)

_ORG_DATA = yaml.safe_load(
    pkgutil.get_data('goal_tools',
                     'organizations.yaml').decode('utf-8')
)


class Organizations:

    _ENDINGS = [
        'Inc',
        'Ltd',
        'Co',
        'LLC',
        'GmbH',
        'Srl',
        'Limited',
        'Corporation',
        'Corp',
    ]

    _BOTS = set([
        'no-reply@openstack.org',
        'infra-root@openstack.org',
    ])

    def __init__(self, data=_ORG_DATA):
        self._data = data
        self._reverse = {
            str(alias).lower(): entry['company_name']
            for entry in self._data
            for alias in entry.get('aliases', [])
        }
        self._reverse.update({
            str(entry['company_name']).lower(): entry['company_name']
            for entry in self._data
        })
        self._domains = {
            domain.lower(): entry['company_name']
            for entry in self._data
            for domain in entry.get('domains', [])
        }

    @functools.lru_cache(maxsize=1024)
    def __getitem__(self, name):
        return self._reverse.get(name.lower(), name)

    @functools.lru_cache(maxsize=1024)
    def from_email(self, email):
        if email in self._BOTS:
            return 'Automation'
        domain = email.partition('@')[-1].lower()
        return self._domains.get(domain)
