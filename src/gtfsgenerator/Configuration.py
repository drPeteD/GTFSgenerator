__author__ = 'frazierb'

import os.path
import configparser
from termcolor import colored

class Configuration(object):

    def __init__(self, config_file=None):

        self._config_parser = configparser.RawConfigParser()
        self._default_config_file = os.path.join(os.path.expanduser('~'), '.gtfsgenerator-default.cfg')

        defaults = None

        if config_file is None:

            print(colored('User did not provide a config file @ cmdline', 'cyan'))

            if (os.path.isfile(self._default_config_file)):
                print(colored("Found default config file located in $HOME", 'cyan'))
                defaults = self._get_defaults_from_conf_file(self._default_config_file)

            else:
                print(colored('Default config file located in $HOME was NOT found', 'red'))
                self._write_default_config()
                print(colored('Created a new config file located @ $HOME', 'cyan'))
                defaults = self._get_defaults_from_conf_file(self._default_config_file)
        else:

            if (os.path.isfile(config_file)):

                defaults = self._get_defaults_from_conf_file(config_file)

            else:
                print("Referenced file is not a valid configuration file")

        self._defaults = defaults

    def _write_default_config(self):

        git_root = os.path.join(os.path.expanduser('~/Documents'), 'Git')

        section1 = 'user'
        self._config_parser.add_section(section1)

        #using njrati.marketing@gmail.com acct. client_id and client_secret
        self._config_parser.set(section1, 'client_id',  'get_key_from_google.apps.googleusercontent.com')
        self._config_parser.set(section1, 'client_secret', 'get_secret_from_Google_dev_dashboard')
        self._config_parser.set(section1, 'client_scope', 'https://www.googleapis.com/auth/drive https://spreadsheets.google.com/feeds https://docs.google.com/feeds')
        self._config_parser.set(section1, 'redirect_uri', 'http://localhost')
        self._config_parser.set(section1, 'oauth_cred_file_name', '.gtfsgenerator.dat')
        self._config_parser.set(section1, 'bing_api_key', 'api_key_from_Google')

        section2 = 'source'
        self._config_parser.add_section(section2)
        self._config_parser.set(section2, 'source_path', git_root + '/gtfsgenerator/test')
        self._config_parser.set(section2, 'stops_source_file', 'stops.csv')
        self._config_parser.set(section2, 'workbook_path', git_root + '/gtfsgenerator/test')
        self._config_parser.set(section2, 'workbook_name', 'test.xlsx')
        self._config_parser.set(section2, 'google_worksheet', 'some_google_url')
        self._config_parser.set(section2, 'wb_header_idx', '6')
        self._config_parser.set(section2, 'exceptions_path', git_root + 'gtfsgenerator/test/reports')
        self._config_parser.set(section2, 'exceptions_filename', 'exceptions.txt')

        section3 = 'gtfs'
        self._config_parser.add_section(section3)
        self._config_parser.set(section3, 'source_path', git_root + '/gtfsgenerator/test/gtfs')
        self._config_parser.set(section3, 'feed_filename', 'feed_info.txt')
        self._config_parser.set(section3, 'agency_filename', 'agency.txt')
        self._config_parser.set(section3, 'stops_filename', 'stops.txt')
        self._config_parser.set(section3, 'stop_times_filename', 'stop_times.txt')
        self._config_parser.set(section3, 'dist_units', 'miles')  # choices miles, kilometers, feet, meters

        section4 = 'agency'
        self._config_parser.add_section(section4)
        self._config_parser.set(section4, 'agency_name', 'My Regional Transportation Authority')
        self._config_parser.set(section4, 'agency_url', 'http://www.daileyplanet.us')
        self._config_parser.set(section4, 'agency_timezone', 'America/New_York')
        self._config_parser.set(section4, 'agency_id', 'DrPete')
        self._config_parser.set(section4, 'agency_lang', 'en')
        self._config_parser.set(section4, 'agency_phone', '(304)558-9324')
        self._config_parser.set(section4, 'agency_phone', 'http://www.wv.gov')

        section5 = 'feed'
        self._config_parser.add_section(section5)
        self._config_parser.set(section5, 'feed_publisher_name', 'Dr.Pete.Dailey@gmail.com')
        self._config_parser.set(section5, 'feed_publisher_url', 'http://www.wv.gov')
        self._config_parser.set(section5, 'feed_lang', 'en')
        self._config_parser.set(section5, 'feed_start_date', '20160101')
        self._config_parser.set(section5, 'feed_end_date', '20161231')
        self._config_parser.set(section5, 'feed_version', '20160228.10')

        with open(self._default_config_file, 'w') as configfile:
            self._config_parser.write(configfile)

    def _get_defaults_from_conf_file(self, conf_file):

        defaults = {}

        if (os.path.isfile(conf_file)):
            self._config_parser.read(conf_file)
            sections = self._config_parser.sections()
            for section in sections:
                for entry in self._config_parser.items(section):
                    defaults[entry[0]] = entry[1]

        return defaults

    def get_defaults(self):
        return self._defaults
