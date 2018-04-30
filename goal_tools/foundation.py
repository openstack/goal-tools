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
    "A Foundation member relationship to an employer"

    def __init__(self, data):
        self._data = data

    @property
    def organization(self):
        "The name of the employer"
        return self._data['organization']['name']

    @property
    def is_current(self):
        "Boolean indicating if the affiliation is set to be current"
        return self._data.get('is_current', False)

    @property
    def start_date(self):
        "Start date of affiliation, if given"
        start = self._data['start_date']
        if start:
            return datetime.datetime.utcfromtimestamp(start)
        return None

    @property
    def end_date(self):
        "End date of affiliation, if given"
        end = self._data['end_date']
        if end:
            return datetime.datetime.utcfromtimestamp(end)
        return None

    def active(self, when):
        """Is the affiliation was in effect on the date specified.

        If we have a current affiliation without start and end dates,
        assume it is active.

        Otherwise the start date and end dates are compared to the
        date provided to determine if it falls within the inclusive
        range.

        Although the argument needs to be a datetime instance, only
        the date portion is used for comparison. We assume that
        someone does not change affiliations on the same day.

        :param when: The date to check for active status
        :type when: datetime.datetime

        """
        if not self.start_date and not self.end_date and self.is_current:
            return True
        if self.start_date and self.start_date.date() > when.date():
            return False
        if self.end_date and self.end_date.date() < when.date():
            return False
        return True


class Member:
    "A person who is a member of the Foundation"

    def __init__(self, email, data):
        self.email = email
        self._data = data

    @property
    def name(self):
        "The person's full name"
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
    LOG.debug('looking up %s', email)
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
    decoded = apis.decode_json(raw)
    try:
        return decoded['data'][0]
    except (KeyError, IndexError):
        return None


def fetch_member(email, cache):
    """Find the member in the cache or look it up in the API.

    :param email: Email address of the member to look for.
    :type email: str
    :param cache: Storage for repeated lookups.
    :type cache: goal_tools.cache.Cache

    """
    key = ('member', email)
    if key in cache:
        LOG.debug('found %s cached', email)
        data = cache[key]
    else:
        data = lookup_member(email)
        if data:
            cache[key] = data
    if data:
        return Member(email, data)
    return None
