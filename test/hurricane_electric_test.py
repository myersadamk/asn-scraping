#!/usr/bin/env python

from unittest import TestCase
from hurricane_electric import CountryAsnReport, ActiveAsnDirectory
import bs4


class SoupableTestFixture():
    blank_soup = '<html><head /><body /></html>'

    def set_soup(self, instance, soup):
        instance.__class__.soup = bs4.BeautifulSoup(soup, 'html.parser')


class CountryAsnReportTest(SoupableTestFixture, TestCase):

    def setUp(self):
        self.report = CountryAsnReport('US')

    def test_no_active_asns_returns_empty(self):
        self.set_soup(self.report, self.blank_soup)
        self.assertEqual(self.report.get_asn_report(), {})

    def test_active_asns_parse_correctly(self):
        report = CountryAsnReport('US')
        self.set_soup(
            self.report,
            '<table id="asns"><tbody><tr>'
            '<td>AS123</td>'
            '<td>Some Company</td>'
            '<td>1</td>'  # Skipped - irrelevant data 
            '<td>2</td>'
            '<td>3</td>'  # Skipped - irrelevant data
            '<td>4</td>'
            '</tr></tbody></table>'
        )
        self.assertEqual(self.report.get_asn_report(), {
            '123': {
                'Country': 'US', 'Name': 'Some Company', 'Routes v4': 2, 'Routes v6': 4
            }
        })


class ActiveAsnDirectoryTest(SoupableTestFixture, TestCase):

    def setUp(self):
        self.directory = ActiveAsnDirectory()

    def test_no_report_links_returns_empty(self):
        self.set_soup(self.directory, self.blank_soup)
        self.assertEqual(self.directory.get_reports(), [])

    def test_no_report_links_returns_empty_when_country_code_provided(self):
        self.set_soup(self.directory, self.blank_soup)
        self.assertEqual(self.directory.get_reports('US'), [])

    def test_multiple_report_links_found(self):
        self.set_soup(
            self.directory,
            '<a href="/country/US">'
            '<a href="/country/UK">'
            '<a href="/country/DE">'
        )

        found_country_codes = map(
            lambda report: report._country_code,
            self.directory.get_reports()
        )
        self.assertEqual(found_country_codes, ['US', 'UK', 'DE'])

    def test_multiple_report_links_found_when_country_code_provided(self):
        self.set_soup(
            self.directory,
            '<a href="/country/US">'
            '<a href="/country/UK">'
            '<a href="/country/DE">'
        )

        found_country_codes = map(
            lambda report: report._country_code,
            self.directory.get_reports('US', 'DE')
        )
        self.assertEqual(['US', 'DE'], found_country_codes)
