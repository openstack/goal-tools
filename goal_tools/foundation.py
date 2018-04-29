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

import datetime
import logging

from goal_tools import apis

LOG = logging.getLogger(__name__)

# The OpenStack foundation member directory lookup API endpoint
MEMBER_LOOKUP_URL = 'https://openstackid-resources.openstack.org/'


class Affiliation:

    def __init__(self, data):
        self._data = data

    @property
    def organization(self):
        return self._data['organization']['name']

    @property
    def is_current(self):
        return self._data.get('is_current', False)

    @property
    def start_date(self):
        start = self._data['start_date']
        if start:
            return datetime.datetime.utcfromtimestamp(start)
        return None

    @property
    def end_date(self):
        end = self._data['end_date']
        if end:
            return datetime.datetime.utcfromtimestamp(end)
        return None

    def active(self, when):
        LOG.debug('checking active %s (%s - %s) against %s',
                  self.organization, self.start_date, self.end_date,
                  when)
        if not self.start_date and not self.end_date and self.is_current:
            return True
        # Compare only the date portion so we don't have to worry
        # about the time of day.
        if self.start_date and self.start_date.date() > when.date():
            LOG.debug('started too late')
            return False
        if self.end_date and self.end_date.date() < when.date():
            LOG.debug('ended too soon')
            return False
        return True


class Member:

    def __init__(self, email, data):
        self.email = email
        self._data = data

    @property
    def name(self):
        return ' '.join([self._data['first_name'], self._data['last_name']])

    @property
    def affiliations(self):
        return (Affiliation(d) for d in self._data['affiliations'])

    @property
    def current_affiliation(self):
        for affiliation in self.affiliations:
            if affiliation.is_current:
                return affiliation

    def find_affiliation(self, when):
        for affiliation in self.affiliations:
            if affiliation.active(when):
                return affiliation


def lookup_member(email):
    "A requests wrapper to querying the OSF member directory API"
    # URL pattern for querying foundation members by E-mail address
    raw = apis.requester(
        MEMBER_LOOKUP_URL + '/api/public/v1/members',
        params={
            'filter[]': [
                'group_slug==foundation-members',
                'email==' + email,
            ],
            'expand': 'all_affiliations',
        },
        headers={'Accept': 'application/json'},
    )

    return apis.decode_json(raw)['data'][0]


def fetch_member(email, cache):
    key = ('member', email)
    if key in cache:
        LOG.debug('found %s cached', email)
        data = cache[key]
    else:
        data = lookup_member(email)
        cache[key] = data
    if data:
        return Member(email, data)
    return None
