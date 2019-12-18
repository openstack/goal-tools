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

import csv
import io
import subprocess

from cliff import lister

from goal_tools import foundation


class ShowTeam(lister.Lister):
    "Show information about review team members"

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'team',
            help='gerrit team name',
        )
        return parser

    def take_action(self, parsed_args):
        member_factory = foundation.MemberFactory({})

        # NOTE(dhellmann): Querying the group APIs requires
        # authentication, so this uses ssh instead of REST because I
        # assume that auth is already set up.
        data = subprocess.check_output(
            ['ssh', 'review.opendev.org', '-p', '29418',
             'gerrit', 'ls-members', parsed_args.team])
        text = data.decode('utf-8')

        reader = csv.DictReader(io.StringIO(text), dialect='excel-tab')

        columns = (
            'Name',
            'Email',
            'Affiliation',
        )

        def get_members():
            for row in reader:
                member = member_factory.fetch(row['email'])
                if member:
                    affiliation = member.current_affiliation.organization
                else:
                    affiliation = None
                yield (row['full name'], row['email'], affiliation)

        return (columns, get_members())
