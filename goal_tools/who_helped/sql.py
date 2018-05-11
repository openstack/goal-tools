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
import os.path
import sqlite3

from goal_tools.who_helped import report

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
            cursor.executemany(SQL_INSERT, data)
        else:
            cursor = db.cursor()

        LOG.debug('querying')
        cursor.execute(parsed_args.query)
        col_names = (info[0] for info in cursor.description)
        return (col_names, cursor.fetchall())
