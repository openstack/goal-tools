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

import itertools
import logging

from cliff import columns
from cliff import lister

from goal_tools import foundation
from goal_tools import gerrit
from goal_tools import governance
from goal_tools import organizations
from goal_tools import utils

LOG = logging.getLogger(__name__)


class DateColumn(columns.FormattableColumn):
    "Format a datetime.datetime to make it serializable."

    def human_readable(self):
        return str(self._value)

    def machine_readable(self):
        return str(self._value)


_COLUMNS = (
    'Review', 'URL', 'Branch',
    'Project', 'Team', 'Official',
    'Role', 'Name', 'Email', 'Date',
    'Organization',
)


class ListContributions(lister.Lister):
    "List the contributions to a set of reviews."

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--governance-project-list',
            default=governance.PROJECTS_LIST,
            help='location of governance project list',
        )
        parser.add_argument(
            '--include-plus-one',
            default=False,
            action='store_true',
            help='include +1 votes',
        )
        parser.add_argument(
            'review_list',
            nargs='+',
            help='name(s) of files containing reviews to include in report',
        )
        return parser

    def take_action(self, parsed_args):

        def make_rows():
            team_data = governance.Governance(
                url=parsed_args.governance_project_list)

            member_factory = foundation.MemberFactory(self.app.cache)
            review_factory = gerrit.ReviewFactory(self.app.cache)
            canonical_orgs = organizations.Organizations()

            review_ids = utils.unique(
                gerrit.parse_review_lists(parsed_args.review_list)
            )

            for review_id in review_ids:

                review = review_factory.fetch(review_id)

                team_name = team_data.get_repo_owner(review.project)

                if parsed_args.include_plus_one:
                    participants = itertools.chain(
                        review.participants,
                        review.plus_ones,
                    )
                else:
                    participants = review.participants

                for participant in participants:

                    # Figure out which organization the user was
                    # affiliated with at the time of the work.
                    organization = None
                    member = member_factory.fetch(participant.email)
                    if member:
                        affiliation = member.find_affiliation(participant.date)
                        if affiliation and affiliation.organization:
                            organization = canonical_orgs[
                                affiliation.organization]
                    else:
                        organization = canonical_orgs.from_email(
                            participant.email)
                    if not organization:
                        organization = "*unknown"

                    yield (
                        review_id,
                        review.url,
                        review.branch,
                        review.project,
                        team_name or '*unknown',
                        'yes' if team_name else 'no',
                        participant.role,
                        participant.name,
                        participant.email,
                        DateColumn(participant.date),
                        organization,
                    )

        return (_COLUMNS, make_rows())
