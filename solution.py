#!/usr/bin/env python

#
# Web scraping
# ASNs (Autonomous System Numbers) are one of the building blocks of the
# Internet. This project is to create a mapping from each ASN in use to the
# company that owns it. For example, ASN 36375 is used by the University of
# Michigan - http://bgp.he.net/AS36375
#
# The site http://bgp.he.net/ has lots of useful information about ASNs.
# Starting at http://bgp.he.net/report/world crawl and scrape the linked country
# reports to make a structure mapping each ASN to info about that ASN.
# Sample structure:
#   {3320: {'Country': 'DE',
#     'Name': 'Deutsche Telekom AG',
#     'Routes v4': 13547,
#     'Routes v6': 268},
#    36375: {'Country': 'US',
#     'Name': 'University of Michigan',
#     'Routes v4': 14,
#     'Routes v6': 1}}
#
# When done, output the collected data to a json file.
#
# Use any python libraries. One suggestion, a good one for scraping is
# BeautifulSoup:
# http://www.crummy.com/software/BeautifulSoup/bs4/doc/
#
import re
from urllib2 import Request, urlopen
from itertools import izip
import bs4
from json import dumps


class AutonomousSystemNumber:
    name = ''
    country = ''
    v4RouteCount = 0
    v6RouteCount = 0

    def __init__(self, name, country, v4RouteCount, v6RouteCount):
        self.name = name
        self.country = country
        self.v4RouteCount = v4RouteCount
        self.v6RouteCount = v6RouteCount

    def toJSON(self):
        return dumps(self.__dict__)


class ReportsTable:

    report_link_regex = re.compile('^/country/([A-Z]+)')
    report_link_attrs = {'href': report_link_regex}

    url = 'http://bgp.he.net/report/world'
    soup = ''

    def __init__(self):
        self.soup = self.__url_to_soup()

    def get_report_urls(self):
       return map(
            lambda element: re.match(self.report_link_regex, element.attrs['href']).group(0),
                  soup.find_all(name='a', attrs=self.report_link_attrs)
       )

    # Given url, return soup.
    def __url_to_soup(self):
        # bgp.he.net filters based on user-agent.
        html = urlopen(Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})).read()
        return bs4.BeautifulSoup(html, 'html.parser')

soup = ReportsTable().soup;
# print soup.prettify()

print ReportsTable().get_report_urls()

# bs4.element.Tag.attrs['href']

# elements = soup.find_all(name='a', attrs=ReportsTable.report_link_attrs)
# for element in elements:
#     print element.attrs['href']
#     print type(element)
#     print re.match(ReportsTable.report_link_regex, element)
