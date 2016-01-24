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

        git_root = os.path.join(os.path.expanduser('~'), 'myGit')

        section1 = 'user'
        self._config_parser.add_section(section1)

        #using njrati.marketing@gmail.com acct. client_id and client_secret
        self._config_parser.set(section1, 'client_id',
                                '1048555667168-0t383qagqukq2jn250h7s6gf3utvpjmi.apps.googleusercontent.com')
        self._config_parser.set(section1, 'client_secret', 'bcs3b4T_IXX4_NDwEpspb5_F')
        self._config_parser.set(section1, 'client_scope', 'https://www.googleapis.com/auth/drive https://spreadsheets.google.com/feeds https://docs.google.com/feeds')
        self._config_parser.set(section1, 'redirect_uri', 'http://localhost')
        self._config_parser.set(section1, 'oauth_cred_file_name', '.gtfsgenerator.dat')
        self._config_parser.set(section1, 'bing_api_key',
                                'Ahstxtcm0xHi2j_FzNLShga3xtBll__EpFGog3usauwf4WpfV4UtaRwlGHw7aCi2')

        section2 = 'source'
        self._config_parser.add_section(section2)
        self._config_parser.set(section2, 'source_path', git_root + '/gtfsgenerator-vmd-proj/testing/source')
        self._config_parser.set(section2, 'stops_source_file', 'stops.csv')
        self._config_parser.set(section2, 'workbook_path', git_root + '/gtfsgenerator-cmd-proj/testing/data_source')
        self._config_parser.set(section2, 'workbook_name', 'woodward_test.xlsx')
        self._config_parser.set(section2, 'google_worksheet', 'some_google_url')
        self._config_parser.set(section2, 'wb_header_idx', '6')
        self._config_parser.set(section2, 'exceptions_path', git_root + 'gtfs_generator-cmd-proj/testing/output')
        self._config_parser.set(section2, 'exceptions_filename', 'exceptions.csv')

        section3 = 'gtfs'
        self._config_parser.add_section(section3)
        self._config_parser.set(section3, 'source_path', git_root + '/gtfsgenerator-vmd-proj/testing/gtfs')
        self._config_parser.set(section3, 'feed_filename', 'feed_info.txt')
        self._config_parser.set(section3, 'agency_filename', 'agency.txt')
        self._config_parser.set(section3, 'stops_filename', 'stops.txt')
        self._config_parser.set(section3, 'stop_times_filename', 'stop_times.txt')
        self._config_parser.set(section3, 'dist_units', 'miles')  # choices miles, kilometers

        section4 = 'agency'
        self._config_parser.add_section(section4)
        self._config_parser.set(section4, 'agency_name', 'Kanawha Valley Regional Transportation Authority')
        self._config_parser.set(section4, 'agency_url', 'http://www.rideonkrt.com')
        self._config_parser.set(section4, 'agency_timezone', 'America/New_York')
        self._config_parser.set(section4, 'agency_id', 'krt')
        self._config_parser.set(section4, 'agency_lang', 'en')
        self._config_parser.set(section4, 'agency_phone', '(304)343-7586')
        self._config_parser.set(section4, 'agency_phone', 'http://www.rideonkrt.com/site/fare-info.html')

        section5 = 'feed'
        self._config_parser.add_section(section5)
        self._config_parser.set(section5, 'feed_publisher_name', 'Dr.Pete.Dailey@gmail.com')
        self._config_parser.set(section5, 'feed_publisher_url', 'http://transit.njrati.org')
        self._config_parser.set(section5, 'feed_lang', 'en')
        self._config_parser.set(section5, 'feed_start_date', '20160101')
        self._config_parser.set(section5, 'feed_end_date', '20161231')
        self._config_parser.set(section5, 'feed_version', '20150624.1')

        section6 = 'stops'
        self._config_parser.add_section(section6)
        self._config_parser.set(section6, 'stops_path_source', '')

        section7 = 'schedules'


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
