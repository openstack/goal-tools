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

from cliff import show

from goal_tools import foundation


class ShowMember(show.ShowOne):
    "Show a Foundation member's basic information."

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'email',
            help='email address of Foundation member',
        )
        return parser

    def take_action(self, parsed_args):
        columns = (
            'Name',
            'Email',
            'Affiliation',
        )
        member_factory = foundation.MemberFactory({})
        member = member_factory.fetch(parsed_args.email)
        if not member:
            raise RuntimeError('Unknown member {}'.format(parsed_args.email))
        return (
            columns,
            (member.name,
             member.email,
             member.current_affiliation.organization),
        )
