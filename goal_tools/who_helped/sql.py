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
import os.path
import sqlite3

from cliff import command

from goal_tools.who_helped import report
from goal_tools import foundation
from goal_tools import gerrit
from goal_tools import governance
from goal_tools import organizations

LOG = logging.getLogger(__name__)


SQL_CREATE = """
create table contribution (
  review text,
  url text,
  branch text,
  project text,
  team text,
  role text,
  name text,
  email text,
  date date,
  organization text
);
"""

SQL_INSERT = """
insert into contribution (
  review, url, branch, project, team, role, name, email,
  date, organization
)
values (
  :Review, :URL, :Branch, :Project, :Team, :Role, :Name, :Email,
  :Date, :Organization
)
"""


class QueryContributions(report.ContributionsReportBase):
    "Run an SQL query against the dataset."

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            '--query', '--sql',
            dest='query',
            help='SQL query to run',
        )
        parser.add_argument(
            '--db',
            default=':memory:',
            help='database to create',
        )
        return parser

    def take_action(self, parsed_args):

        db_is_new = not os.path.exists(parsed_args.db)
        db = sqlite3.connect(parsed_args.db)
        if db_is_new:
            db.execute(SQL_CREATE)

            data = self.get_contributions(parsed_args)

            cursor = db.cursor()
            print(SQL_INSERT)
            data = list(data)
            print('DATA[0]:', data[0])
            cursor.executemany(SQL_INSERT, data)
        else:
            cursor = db.cursor()

        LOG.debug('querying')
        cursor.execute(parsed_args.query)
        col_names = (info[0] for info in cursor.description)
        return (col_names, cursor.fetchall())


class DBCreate(command.Command):
    "Build a local database of contributions."

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
            '--include-plus-one',
            default=False,
            action='store_true',
            help='include +1 votes',
        )
        parser.add_argument(
            '--force',
            default=False,
            action='store_true',
            help='force recreating the database',
        )
        parser.add_argument(
            'query_string',
            help='gerrit query string',
        )
        parser.add_argument(
            'db_file',
            help='database to create',
        )
        return parser

    def take_action(self, parsed_args):
        team_data = governance.Governance(
            url=parsed_args.governance_project_list)

        cache = self.app._load_cache_file(preload=False)
        factory = gerrit.ReviewFactory(cache)
        member_factory = foundation.MemberFactory(cache)
        canonical_orgs = organizations.Organizations()

        if os.path.exists(parsed_args.db_file):
            if not parsed_args.force:
                print('ERROR: {} already exists. '
                      'Use the --force flag to overwrite.'.format(
                          parsed_args.db_file))
                return 1
            else:
                os.unlink(parsed_args.db_file)

        db = sqlite3.connect(parsed_args.db_file)
        db.execute(SQL_CREATE)

        def get_data():
            review_source = factory.query(parsed_args.query_string)
            for review in review_source:

                team_name = team_data.get_repo_owner(review.project)

                if not parsed_args.include_unofficial and not team_name:
                    LOG.debug(
                        'filtered out %s based on repo governance status',
                        review.project,
                    )
                    continue

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

                    yield (review.id, review.url, review.branch,
                           review.project, team_name, participant.role,
                           participant.name, participant.email,
                           participant.date, organization)

        cursor = db.cursor()
        data = get_data()
        while True:
            chunk = list(itertools.islice(data, 100))
            if not chunk:
                break
            LOG.debug('inserting %d', len(chunk))
            cursor.executemany(SQL_INSERT, chunk)
            db.commit()
