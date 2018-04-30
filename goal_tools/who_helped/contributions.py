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
from goal_tools import governance
from goal_tools import utils

LOG = logging.getLogger(__name__)


class DateColumn(columns.FormattableColumn):
    "Format a datetime.datetime to make it serializable."

    def human_readable(self):
        return str(self._value)

    def machine_readable(self):
        return str(self._value)


class ListContributions(lister.Lister):
    "List the contributions to a set of reviews."

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--role',
            default=[],
            action='append',
            help='filter to only include specific roles (may be repeated)',
        )
        parser.add_argument(
            '--governance-project-list',
            default=governance.PROJECTS_LIST,
            help='location of governance project list',
        )
        parser.add_argument(
            '--include-unofficial',
            default=False,
            action='store_true',
            help='include projects not under governance in the output',
        )
        parser.add_argument(
            'review_list',
            nargs='+',
            help='name(s) of files containing reviews to include in report',
        )
        return parser

    def take_action(self, parsed_args):
        columns = (
            'Review ID', 'Review URL', 'Project', 'Team',
            'Role', 'Name', 'Email', 'Date',
            'Organization',
        )

        def make_rows():
            team_data = governance.get_team_data(
                parsed_args.governance_project_list)

            roles = parsed_args.role
            cache = self.app.cache
            include_unofficial = parsed_args.include_unofficial

            review_ids = utils.unique(
                gerrit.parse_review_lists(parsed_args.review_list)
            )

            for review_id in review_ids:

                review = gerrit.fetch_review(review_id, cache)

                for participant in review.participants:

                    if roles and participant.role not in roles:
                        LOG.debug('filtered out %s based on role', participant)
                        continue

                    team_name = governance.get_repo_owner(
                        team_data, review.project)

                    if not team_name and not include_unofficial:
                        LOG.debug(
                            'filtered out %s based on repo governance status',
                            review.project,
                        )
                        continue

                    # Figure out which organization the user was
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
                        review.project,
                        team_name,
                        participant.role,
                        participant.name,
                        participant.email,
                        DateColumn(participant.date),
                        organization,
                    )

        return (columns, make_rows())