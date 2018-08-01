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

import bs4 as beautifulsoup
import requests

_SITE_TITLE = '— OpenStack Technical Committee Governance Documents'


def _parse_goal_page(html):
    data = {
        'title': '',
        'description': '',
    }
    bs = beautifulsoup.BeautifulSoup(html, 'html.parser')
    data['title'] = bs.title.string or ''
    if data['title'].endswith(_SITE_TITLE):
        data['title'] = data['title'][:-len(_SITE_TITLE)].strip()
    data['description'] = bs.p.text or bs.p.string or ''
    return data


def get_info(url):
    html = requests.get(url)
    data = _parse_goal_page(html.text)
    data['url'] = url
    return data
