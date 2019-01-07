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

from cliff import command

from goal_tools import gerrit
from goal_tools import governance

LOG = logging.getLogger(__name__)


class QueryChanges(command.Command):
    "Query gerrit for a set of changes and build a review ID file."

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
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
            'query_string',
            help='gerrit query string',
        )
        parser.add_argument(
            'review_list',
            help='name output file to create',
        )
        return parser

    def take_action(self, parsed_args):
        team_data = governance.Governance(
            url=parsed_args.governance_project_list)

        review_ids = []

        cache = self.app._load_cache_file(preload=False)

        factory = gerrit.ReviewFactory(cache)

        review_source = factory.query(parsed_args.query_string)
        for review in review_source:
            team_name = team_data.get_repo_owner(review.project)
            if not parsed_args.include_unofficial and not team_name:
                LOG.debug(
                    'filtered out %s based on repo governance status',
                    review.project,
                )
                continue
            review_ids.append(review.id)

        with open(parsed_args.review_list, 'w', encoding='utf-8') as f:
            f.write('# QUERY: {}\n'.format(
                parsed_args.query_string.replace('\n', ' ')))
            for rid in sorted(review_ids):
                f.write('{}\n'.format(rid))
