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
from re import compile, match
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


class Soupable(object):
    def __init__(self, url):
        self.url = url

    @property
    def soup(self):
        # bgp.he.net filters based on user-agent.
        html = urlopen(Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})).read()
        return bs4.BeautifulSoup(html, 'html.parser')


class AsnReport(Soupable):
    url = 'https://bgp.he.net/country/'

    def __init__(self, country_code):
        self.url += country_code
        self.country_code = country_code
        super(AsnReport, self).__init__(self.url)


class ReportsTable(Soupable):
    report_link_regex = compile('^/country/([A-Z]+)')
    report_link_attrs = {'href': report_link_regex}

    def __init__(self):
        super(ReportsTable, self).__init__('http://bgp.he.net/report/world')

    def get_reports(self):
        def report_from_report_link_element(element):
            AsnReport(match(self.report_link_regex, element.attrs['href']).group(1))

        return map(
            lambda element: report_from_report_link_element(element),
            self.soup.find_all(name='a', attrs=self.report_link_attrs)
        )


# for r in ReportsTable().get_reports(): print r.country_code
# for r in ReportsTable().get_reports(): print r.soup
# print AsnReport('DE').soup.prettify()
print AsnReport('DE').soup.prettify()
