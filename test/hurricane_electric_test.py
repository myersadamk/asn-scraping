#!/usr/bin/env python
from os import listdir, path
from unittest import TestCase
from hurricane_electric import CountryAsnReport, ActiveAsnDirectory, ActiveAsnReportGenerator
from json import load
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
        self._directory = ActiveAsnDirectory()

    def test_no_report_links_returns_empty(self):
        self.set_soup(self._directory, self.blank_soup)
        self.assertEqual(self._directory.get_reports(), [])

    def test_no_report_links_returns_empty_when_country_code_provided(self):
        self.set_soup(self._directory, self.blank_soup)
        self.assertEqual(self._directory.get_reports('US'), [])

    def test_multiple_report_links_found(self):
        self.set_soup(
            self._directory,
            '<a href="/country/US">'
            '<a href="/country/UK">'
            '<a href="/country/DE">'
        )

        found_country_codes = map(
            lambda report: report._country_code,
            self._directory.get_reports()
        )
        self.assertEqual(found_country_codes, ['US', 'UK', 'DE'])

    def test_multiple_report_links_found_when_country_code_provided(self):
        self.set_soup(
            self._directory,
            '<a href="/country/US">'
            '<a href="/country/UK">'
            '<a href="/country/DE">'
        )

        found_country_codes = map(
            lambda report: report._country_code,
            self._directory.get_reports('US', 'DE')
        )
        self.assertEqual(['US', 'DE'], found_country_codes)


class HurricaneElectricIntegrationTest(TestCase):
    _REPORT_DIR = 'test_reports'

    def setUp(self):
        self._report_generator = ActiveAsnReportGenerator(report_dir=self._REPORT_DIR)
        self._report_generator.clear_asn_reports()

    def tearDown(self):
        self._report_generator.clear_asn_reports()

    def test_write_US_asn_report(self):
        self.assertEqual(listdir(self._REPORT_DIR).__len__(), 0)
        self._report_generator.write_asn_report('US')

        reports = listdir(self._REPORT_DIR)
        self.assertEqual(reports.__len__(), 1)

        with open(path.join(self._REPORT_DIR, reports[0]), 'r') as report:
            for asn in load(report).values():
                self.assertEqual('US', asn['Country'])
                self.assertNotEqual(0, asn['Name'].__len__())
                self.assertEqual(unicode, type(asn['Name']))
                self.assertEqual(int, type(asn['Routes v4']))
                self.assertEqual(int, type(asn['Routes v6']))
