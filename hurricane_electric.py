#!/usr/bin/env python

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

from datetime import datetime
from json import dumps
from os import path, curdir, listdir, mkdir, remove
from re import compile, match
from threading import Thread
from time import time
from urllib2 import Request, urlopen
import argparse

from bs4 import BeautifulSoup


# Mixin for objects that can be represented as HTML pages.
class Soupable(object):
    def __init__(self, url):
        self.url = url

    @property
    def soup(self):
        # bgp.he.net filters based on user-agent.
        html = urlopen(Request(self.url, headers={'User-Agent': 'Mozilla/5.0'})).read()
        return BeautifulSoup(html, 'html.parser')


# Wraps individual Country's active ASN report page, providing screen-scraping functionality that
# retrieves ASN information.
class CountryAsnReport(Soupable):

    def __init__(self, country_code):
        self._country_code = self._to_utf8(country_code)
        super(CountryAsnReport, self).__init__('https://bgp.he.net/country/' + country_code)

    # Returns a report of the active ASNs for the current country in the following object format:
    # { <asn identifier in numeric form>:
    #     'Country': <country code>
    #     'Name': <name of ASN owner>
    #     'Routes v4': <number of v4 routes>
    #     'Routes v6': <number of v6 routes>
    # }
    def get_asn_report(self):
        asn_info_by_asn_id = {}
        table_soup = self.soup.find('table', attrs={'id': 'asns'})

        # Not all countries have active ASNs; in that case, there will be no 'asn' <table> element.
        if table_soup is None:
            return asn_info_by_asn_id

        def parse_numeric(element):
            return int(element.text.replace(',', ''))

        def parse_unicode(element):
            return self._to_utf8(element.text)

        for row in table_soup.find('tbody').find_all('tr'):
            asn_info = row.find_all('td')
            asn_info_by_asn_id[parse_unicode(asn_info[0]).strip('AS')] = {
                'Country': self._country_code,
                'Name': parse_unicode(asn_info[1]),
                'Routes v4': parse_numeric(asn_info[3]),
                'Routes v6': parse_numeric(asn_info[5])
            }

        return asn_info_by_asn_id

    # May be superfluous since the JSON dump removes the unicode-type characters anyway,
    # but helps when consuming the module directly. I'm not sure if it's more idiomatic
    # to just use unicode.
    @staticmethod
    def _to_utf8(unicode_string):
        return unicode_string.encode('utf-8')


# Wraps the main ASN Report listing page, providing screen-scraping functionality for getting
# individual CountryAsnReport instances.
class ActiveAsnDirectory(Soupable):
    _REPORT_LINK_REGEX = compile('/country/([A-Z]+)')

    def __init__(self):
        super(ActiveAsnDirectory, self).__init__('http://bgp.he.net/report/world')

    def get_reports(self, *country_codes):
        def get_report_from_report_link_element(element):
            return CountryAsnReport(match(self._REPORT_LINK_REGEX, element.attrs['href']).group(1))

        def get_country_code_regex(all_countries=self._REPORT_LINK_REGEX):
            return all_countries if country_codes == () else compile('/country/' + "|".join(country_codes))

        return map(
            lambda element: get_report_from_report_link_element(element),
            self.soup.find_all(name='a', attrs={'href': get_country_code_regex()})
        )


class ActiveAsnReportGenerator:

    def __init__(self, reports_table=ActiveAsnDirectory(), report_prefix='asn_report', report_dir='reports'):
        self._reports_table = reports_table
        self._report_prefix = report_prefix
        self._report_dir = report_dir

        if not path.exists(self._report_dir):
            mkdir(self._report_dir)

    def clear_asn_reports(self):
        for report in listdir(path.join(curdir, self._report_dir)):
            remove(path.join(curdir, self._report_dir, report))

    # Writes an ASN report as JSON with the configured instance prefix and directory, returning the generated report
    # dictionary. An existing report can optionally be passed, otherwise it will be generated.
    def write_asn_report(self, report=None, *country_codes):
        def generate_current_timestamp():
            return datetime.fromtimestamp(time()).strftime('%Y_%m_%d_%H_%M_%S')

        report_path = \
            path.join(curdir, self._report_dir, self._report_prefix + '_' + generate_current_timestamp() + '.json')

        if report is None:
            report = self.get_asn_report(*country_codes)
        with open(report_path, 'w') as report_file:
            report_file.write(dumps(report, indent=2, sort_keys=True))

        return report

    # Gets an ASN report for all given country codes, or all listed countries if no country_codes are specified.
    # The format of the report is a dictionary with entries keyed by their numeric ASN numbers; this is basically
    # a dictionary of all respective CountryAsnReport::get_asn_report() as entries.
    def get_asn_report(self, *country_codes):
        final_report = {}

        # Note that I researched this, and dict::update is an atomic operation, and therefore thread-safe.
        def append_asn_report(report):
            final_report.update(report.get_asn_report())

        threads = []

        for current_report in self._reports_table.get_reports(*country_codes):
            thread = Thread(target=append_asn_report, args=(current_report,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        return final_report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--report-prefix',
        default='asn_report',
        help='Defines the output prefix for ASN reports (default: asn_report).'
             'For instance, if the default value is used, the output will be asn_report_TIMESTAMP.json'
    )
    parser.add_argument(
        '--report-dir',
        default='reports',
        help='Defines the output directory for ASN reports (default: ./reports)'
    )
    parser.add_argument(
        '--country-codes',
        nargs='*',
        default=(),
        help='Specifies the country codes (e.g. US DE) to retrieve ASNs for.'
             'If unspecified, all listed countries will be reported.'
    )
    parser.add_argument(
        '--actions',
        nargs='+',
        default=['write'],
        help='Specifies the actions to take. By default, only the "write" action is taken. All actions include:\n'
             '"clear": clears all ASN reports in the specified (or default) report_dir.'
             '"write": writes an ASN report according to the other configurations provided.'
             '"print": prints the ASN report to stdout.'

    )

    args = parser.parse_args()
    generator = ActiveAsnReportGenerator(report_prefix=args.report_prefix, report_dir=args.report_dir)

    if set(args.actions) & set(('write', 'print')):
        report = generator.get_asn_report(*args.country_codes)

    for action in args.actions:
        if action == 'clear':
            generator.clear_asn_reports()
        elif action == 'write':
            generator.write_asn_report(report=report)
        elif action == 'print':
            print dumps(report, indent=2, sort_keys=True)
        else:
            print 'Unrecognized action "' + action + '". This option will be ignored.'
