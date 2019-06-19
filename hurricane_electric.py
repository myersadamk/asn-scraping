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
    _ASN_SUBSTITUTION_REGEX = compile('AS([0-9])+')

    def __init__(self, full_asn, country, name, v4RouteCount, v6RouteCount):
        self._full_asn = full_asn
        self.country = country
        self.name = name
        self.v4RouteCount = v4RouteCount
        self.v6RouteCount = v6RouteCount

    def toJSON(self):
        return dumps({
            'Country': self.country,
            'Name': self.name
        })

    @staticmethod
    def from_soup(table_row_soup):
        asn_info = table_row_soup.find_all('td')


class Soupable(object):
    def __init__(self, url):
        self.url = url

    @property
    def soup(self):
        # bgp.he.net filters based on user-agent.
        html = urlopen(Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})).read()
        return bs4.BeautifulSoup(html, 'html.parser')


class CountryReport(Soupable):
    url = 'https://bgp.he.net/country/'

    def __init__(self, country_code):
        self.url += country_code
        self.country_code = country_code
        super(CountryReport, self).__init__(self.url)

    def get_asn_info_by_asn_id(self):
        asn_info_by_asn_id = {}
        for row in self.soup.find('table', attrs={'id': 'asns'}).find('tbody').find_all('tr'):
            asn_info = row.find_all('td')

            assert asn_info.__len__() == 6

            asn_info_by_asn_id[asn_info[0].text.strip('AS')] = {
                'Country': self.country_code,
                'Name': asn_info[1].text,
                'Routes v4': asn_info[3].text,
                'Routes v6': asn_info[5].text,
            }
        return dumps(asn_info_by_asn_id, indent=2, sort_keys=True)


class AsnReportIndex(Soupable):
    _REPORT_LINK_REGEX = compile('/country/([A-Z]+)')
    _REPORT_LINK_ATTRS = {'href': _REPORT_LINK_REGEX}

    def __init__(self):
        super(AsnReportIndex, self).__init__('http://bgp.he.net/report/world')

    def get_reports(self):
        def get_report_from_report_link_element(element):
            return CountryReport(match(self._REPORT_LINK_REGEX, element.attrs['href']).group(1))

        return map(
            lambda e: get_report_from_report_link_element(e),
            self.soup.find_all(name='a', attrs=self._REPORT_LINK_ATTRS)
        )


class AsnReportParser:

    def __init__(self, reports_table=AsnReportIndex()):
        self._reports_table = reports_table

    def generate_asn_report(self):
        return dumps('')


# for r in AsnReportIndex().get_reports(): print r.country_code
# for r in ReportsTable().get_reports(): print r.soup
# print AsnReport('DE').soup.prettify()
print CountryReport('DE').get_asn_info_by_asn_id()
