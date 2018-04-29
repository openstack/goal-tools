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

import collections
import datetime
import fileinput
import logging
import urllib.parse

from goal_tools import apis

LOG = logging.getLogger(__name__)

# The base URL to Gerrit REST API
GERRIT_API_URL = 'https://review.openstack.org/'


def parse_review_lists(filenames):
    """Generator that produces review IDs as strings.

    Read the files expecting to find one review URL or ID per
    line. Ignore lines that start with # as comments. Ignore blank
    lines.

    :param filenames: Iterable of filenames to read.
    :return: Generator of str

    """
    for line in fileinput.input(filenames):
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            continue
        LOG.debug('parsing %r', line)
        parsed = urllib.parse.urlparse(line)
        if parsed.fragment:
            # https://review.openstack.org/#/c/561507/
            yield parsed.fragment.lstrip('/c').partition('/')[0]
        else:
            # https://review.openstack.org/555353/
            yield parsed.path.lstrip('/').partition('/')[0]


def query_gerrit(method, params={}):
    """Query the Gerrit REST API"""
    url = GERRIT_API_URL + method
    LOG.debug('fetching %s', url)
    raw = apis.requester(
        url, params=params,
        headers={'Accept': 'application/json'})
    return apis.decode_json(raw)


def _to_datetime(s):
    # Ignore the trailing decimal seconds.
    s = s.rpartition('.')[0]
    return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S')


Participant = collections.namedtuple(
    'Participant', ['role', 'name', 'email', 'date'])


class Review:

    def __init__(self, id, data):
        self._id = id
        self._data = data

    @property
    def url(self):
        return GERRIT_API_URL + self._id + '/'

    @property
    def created(self):
        return _to_datetime(self._data['created'])

    @property
    def participants(self):
        yield self.owner
        yield from self.reviewers

    @property
    def owner(self):
        owner = self._data['owner']
        return Participant(
            'owner',
            owner['name'],
            owner['email'],
            self.created,
        )

    @property
    def reviewers(self):
        for label in self._data['labels']['Code-Review']['all']:
            if label['value'] not in (2, -1):
                # Only report reviewers with negative reviews or
                # approvals to avoid counting anyone who is just
                # leaving lots of +1 votes without actually providing
                # feedback.
                continue
            yield Participant(
                'reviewer',
                label['name'],
                label['email'],
                _to_datetime(label['date']),
            )
        for label in self._data['labels']['Workflow']['all']:
            if label.get('value', 0) != 1:
                continue
            yield Participant(
                'approver',
                label['name'],
                label['email'],
                _to_datetime(label['date']),
            )


def fetch_review(review_id, cache):
    key = ('review', review_id)
    if key in cache:
        LOG.debug('found %s cached', review_id)
        data = cache[key]
    else:
        data = query_gerrit('changes/' + review_id + '/detail')
        cache[key] = data
    return Review(review_id, data)
