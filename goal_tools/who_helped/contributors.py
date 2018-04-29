#!/usr/bin/env python3

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

import logging

from cliff import columns
from cliff import lister

from goal_tools import foundation
from goal_tools import gerrit
from goal_tools import utils

LOG = logging.getLogger(__name__)


class DateColumn(columns.FormattableColumn):

    def human_readable(self):
        return str(self._value)

    def machine_readable(self):
        return str(self._value)


class ListContributors(lister.Lister):
    "List the contributors to a set of reviews."

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--role',
            default=[],
            action='append',
            help='filter to only include specific roles (may be repeated)',
        )
        parser.add_argument(
            'review_list',
            nargs='+',
            help='name(s) of files containing reviews to include in report',
        )
        return parser

    def take_action(self, parsed_args):
        columns = (
            'Review ID', 'Review URL', 'Role', 'Name', 'Email', 'Date',
            'Organization',
        )

        def make_rows():
            review_ids = utils.unique(
                gerrit.parse_review_lists(parsed_args.review_list)
            )
            roles = parsed_args.role
            cache = self.app.cache
            for review_id in review_ids:
                review = gerrit.fetch_review(review_id, cache)
                for participant in review.participants:
                    if roles and participant.role not in roles:
                        LOG.debug('filtered out %s based on role', participant)
                        continue

                    # Figure out which organization they were
                    # affiliated with at the time of the work.
                    organization = None
                    member = foundation.fetch_member(participant.email, cache)
                    if member:
                        affiliation = member.find_affiliation(participant.date)
                        if affiliation:
                            organization = affiliation.organization

                    yield (
                        review_id,
                        review.url,
                        participant.role,
                        participant.name,
                        participant.email,
                        DateColumn(participant.date),
                        organization,
                    )

        return (columns, make_rows())
