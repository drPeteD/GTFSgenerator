#!/usr/bin/env python
"""
Copyright (C) Dr. Peter J Dailey

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Python script to:
 1. Read a configuration file containing GTFS agency, feed_info, fare, and service exception values.
 2. Parse a series of turn-by-turn worksheets from a Google Sheets workbook
 3. Decompose KML line files representing route segments into a qualified GTFS shapes.txt entry.

    Usage: gtfsgenerator [cvtdg]
    example, generate feed files from workbook defined in the configuration file 'krt.cfg'
        gtfsgenerator -c configs/krt.cfg --generate
"""

import argparse
import csv
from datetime import datetime
import glob
import fileinput
import os
import subprocess
import sys
from shutil import copyfile
import xml.etree.ElementTree as ET
import zipfile
from os.path import expanduser
import gspread          # read Google sheets
from geopy.distance import vincenty
from oauth2client import tools
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from pytz import common_timezones
from pandas import to_datetime
import pandas as pd
from pandas import read_excel
from termcolor import colored
from veryprettytable import VeryPrettyTable

from gtfsgenerator.Configuration import Configuration
from gtfsgenerator.GTFS import GtfsHeader
from gtfsgenerator.GtfsCalendar import ServiceExceptions


def pretty_print_args(configs):
    """
    Print the configuration arguments in a table
    :param configs: Configuration values from .cfg file
    :return:
    """
    print(colored("\nArguments table:", 'green'))
    arg_table = VeryPrettyTable([colored("Argument Name", 'green'), colored("Value", 'green')])
    arg_table.align["Argument Name"] = "l"
    arg_table.align["Value"] = "r"
    arg_table.padding_width = 2

    # Ref: https://pypi.python.org/pypi/termcolor
    for index, entry in enumerate(configs._get_kwargs()):
        arg_table.add_row([colored(str(entry[0]), 'green'), colored(str(entry[1]), 'red')])

    print(arg_table)


def get_config_parser_for_passed_in_config_file():
    config_parser = argparse.ArgumentParser(
        description=__doc__,  # printed with -h/--help
        # Don't mess with format of description
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # Turn off help, so we print all options in response to -h
        add_help=False
    )

    config_parser.add_argument("-c", "--config_file", help="Specify a config file", metavar="FILE")

    return config_parser


def open_google_workbook(google_workbook_name, defaults, configs):
    """
    Open Google Sheets workbook with oauth2 credentials.
    :param google_workbook_name:
    :param defaults:
    :param configs:
    :return:
    """
    credentials = get_credentials(client_id=defaults.get('client_id'),
                                  client_secret=defaults.get('client_secret'),
                                  client_scope=defaults.get('client_scope'),
                                  redirect_uri=defaults.get('redirect_uri'),
                                  oauth_cred_file_name=defaults.get('oauth_cred_file_name'))

    # Ref: http://www.lovholm.net/2013/11/25/work-programmatically-with-google-spreadsheets-part-2/
    gc = gspread.authorize(credentials)
    # Google workbook name is in the config file. <<< Pass in from config list!
    # route_workbook = gc.open(configs.google_workbook_name) <<< older single workbook
    route_workbook = gc.open(google_workbook_name)

    return route_workbook


def select_spreadsheet_source(filename, configs):
    # ref: http://davidmburke.com/2013/02/13/pure-python-convert-any-spreadsheet-format-to-list/
    # Use xlrd: https://secure.simplistix.co.uk/svn/xlrd/trunk/xlrd/doc/xlrd.html?p=4966
    file_ext = filename[-3:]
    data = []
    if file_ext == "xls":
        import xlrd
        wb = xlrd.open_workbook(filename)
        sh1 = wb.sheet_by_index(0)
        for rownum in range(sh1.nrows):
            data += [sh1.row_values(rownum)]
    elif file_ext == "csv":
        import csv
        reader = csv.reader(open(filename, "rb"))
        for row in reader:
            data += [row]
    # elif file_ext == "lsx":
    #     from openpyxl.reader.excel import load_workbook
    #     wb = load_workbook(filename=filename, use_iterators=True)
    #     sheet = wb.get_active_sheet()
    #     for row in sheet.iter_rows():
    #         data_row = []
    #         for cell in row:
    #             data_row += [cell.internal_value]
    #         data += [data_row]
    # elif file_ext == "ods":
    #     from odsreader import ODSReader
    #     doc = ODSReader(filename)
    #     table = doc.SHEETS.items()[0]
    #     data += table[1]
    return data


def get_credentials(client_id, client_secret, client_scope, redirect_uri, oauth_cred_file_name):
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """

    # TODO: Pass the cred_file_name from args?

    flow = OAuth2WebServerFlow(client_id=client_id, client_secret=client_secret, scope=client_scope,
                               redirect_uri=redirect_uri)

    storage = Storage(os.path.join(os.path.expanduser('~'), oauth_cred_file_name))
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        flags = tools.argparser.parse_args(args=[])
        credentials = tools.run_flow(flow, storage, flags)

    return credentials


def get_output_dir_name(configs):

    # output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'output'))

    output_dir = os.path.expanduser(configs.gtfs_path_root)

    # print('get_output_dir_name ***+++ output_dir-test +++:{}'.format(output_dir))
    # print('get_output_dir_name *** configs.gtfs_path_root ***:{}'.format(configs.gtfs_path_root))
    # output_dir = os.path.abspath(os.path.dirname(configs.gtfs_path_root))
    # print('get_output_dir_name ***> output_dir <---:{}'.format(output_dir))

    return output_dir


def create_output_dir(configs):
    output_dir = get_output_dir_name(configs)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


def get_worksheet_name_output_dir(worksheet_title, configs):
    '''
    Get the fully qualified output directory name from Config file and worksheet title.
    If title is 'master', then use the top level directory from Config file.
    :param worksheet_title:
    :param configs:
    :return:
    '''

    output_dir = get_output_dir_name(configs)
    worksheet_name_output_dir = os.path.join(output_dir, worksheet_title)

    return worksheet_name_output_dir


def create_worksheet_name_output_dir(worksheet_title, configs):

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)

    print('Output directory:{}'.format(worksheet_name_output_dir))
    if not os.path.exists(worksheet_name_output_dir):
        os.makedirs(worksheet_name_output_dir)
        c_note = colored(' Directory does not exist, creating directory {}'.format(worksheet_name_output_dir),color='red')
        print(c_note)
    else:
        print('Existing directory {}'.format(worksheet_name_output_dir))


def write_stop_times_file(worksheet_title, rows, columns, stops, workbook, worksheet, configs):
    """

    0 Tram / Light Rail
    1 Subway / Metro
    2 Rail
    3 Bus
    4 Ferry
    5 Cable Car
    6 Gondola
    7 Funicular

    :param worksheet_title: Tab on worksheet used for folder name.
    :param rows:
    :param columns:
    :param stops: List of stops from previous operation.
    :param worksheet:
    :param configs: Configuration object
    :return:
    """
    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)

    # File header
    x = GtfsHeader()
    x.write_header('stop_times', worksheet_name_output_dir)

    # If the route_type is a bus (route_type 3) then departure and arrival times are identical.
    # If not in spreadsheet, use default from config file.
    if worksheet[2][14]:
        route_type = worksheet[2][14]
    else:
        route_type = configs.default_route_type

    # Setup and clear stop_time list.
    stop_time_data = []
    # Setup loop counter.
    trip_count = 0
    # Hours before midnight. Use to correct for single digit times.
    before_mid = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']
    # Hours after midnight. Use to correct for times after midnight of the same day - see GTFS specs.
    after_mid  = ['0', '00', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36']
    prev_depart_time = ''

    # print('Hours before midnight:{}\nHours after midnight:{}'.format(before_mid, after_mid))
    # Outer loop (by columns) through trips. Trip column start in 27 in worksheet, ends with column: columns[-1]
    for j in range(27, int(columns[-1])):

        # Build trip_id from trip_id plus time header.
        trip_id = '{}-{}'.format(worksheet[1][20], worksheet[2][j])
        # Create a trip.txt entry
        write_trips_file(trip_id, worksheet_name_output_dir, workbook, worksheet, configs)
        trip_count += 1
        # Begining of trip loop, set check to False.
        trip_start_check = False
        prev_depart_time = ''

        # Inner loop by row through stops.
        for i in range(3, len(rows)):

            # Set departure time to empty.
            departure_time = ''
            arrival_time = departure_time

            loc_type = worksheet[i][17]
            # If stop is a station (location_type = 1) skip it. Get location type from worksheet.
            if loc_type == '1':
                continue  # Skip the station, on to the next station.

            # Is this a time point?
            if worksheet[i][j]:
                # Split the time, examin hour.
                hour = worksheet[i][j].split(':')
                print('  Hour {}'.format(hour[0]))
                trip_start_check = True
                if hour[0] in before_mid:
                    if prev_depart_time[:2] in after_mid:
                        departure_time = '{}:{}:{}'.format(int(hour[0]) + 24, hour[1], hour[2])
                        print(colored('Non-standard time. Previous departure time:{}. This departure time:{}'.format(prev_depart_time, departure_time),'blue'))
                    else:
                    # Ensure standard time is properly formatted. Convert to Pandas Timestamp then format string.
                        departure_time = '{}:{}:{}'.format(int(hour[0]), hour[1], hour[2])
                    print(colored('>>Trip start is {}, departure time is {}.'.format(trip_start_check, departure_time), color='blue'))
                if hour[0] in after_mid:
                    if hour[0] == '0' or hour[0] == '00':
                        departure_time = '{}:{}:{}'.format('24', hour[1], hour[2])
                    else:
                        departure_time = '{}:{}:{}'.format( hour[0], hour[1], hour[2])
                    print('Handle time past midnight, time is {}.'.format(departure_time))
                print(colored("  Departure time is {}".format(departure_time),color='green'))
                print(colored('^^^^ Time point, trip:{} {}'.format(trip_id, departure_time), color='green'))
                arrival_time = departure_time
            else:
                departure_time  = ''
                arrival_time    = departure_time

            # Collect all stop_time.txt values
            stop_sequence = '{}'.format(worksheet[i][2])
            stop_id = '{}'.format(worksheet[i][3])
            stop_headsign = worksheet[i][22]
            pickup_type = worksheet[i][23]
            drop_off_type = worksheet[i][24]
            distance_traveled =  worksheet[i][25]

            # TODO Check that end stop in a trip has a time.

            # If trip start is False, then a time point has not been processed. Skip to next row.
            if trip_start_check is True:
                stop_time_line = '{},{},{},{},{},{},{},{},{}'.format(trip_id, arrival_time, departure_time, stop_id, stop_sequence, stop_headsign, pickup_type, drop_off_type,
                                                                     distance_traveled)
                stop_time_data.append('{}\n'.format(stop_time_line))

            # print(colored(' previous dep:{}, this dep:{}'.format(prev_depart_time, departure_time),'green'))
            if departure_time:
                prev_depart_time = departure_time

    # Open and append to file stop_times.txt
    print('Writing stop_times data...')
    gtfs_file = os.path.join(worksheet_name_output_dir, 'stop_times.txt')
    f = open(gtfs_file, "a")
    for stop_time in stop_time_data:
        f.write(stop_time)
    f.close()
    print('Finished stop_times.txt, {} trips.'.format(trip_count))

    return


def write_trips_header(worksheet_title, configs):
    """
    Open and write the header for all the GTFS files.
    Args:
        worksheet_title:
        configs:

    Returns:

    """

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)

    # File header
    x = GtfsHeader()
    x.write_header('trips', worksheet_name_output_dir)


def write_trips_file(trip_id, worksheet_title, workbook, worksheet, configs):
    '''
    Write trips values.

    route_id(r), service_id(r), trip_id(r), trip_headsign, trip_short_name, direction_id, block_id, shape_id,  wheelchair_acesible, bikes_allowed
    :param trip_id:
    :param
    :param
    :return:
    '''

    # Collect all trips.txt values
    value = []

    for i in range(18, 28):
        if worksheet[1][i] is not None:
            value.append(worksheet[1][i])
        else:
            value.append('')

    # print('write_stop_times --> value list:{} '.format(value))

    route_id = '{}'.format(value[0])
    service_id = '{}'.format(value[1])
    # import trip_id from stop_times
    trip_headsign = '{}'.format(value[3])
    # trip_id constructed previously
    trip_short_name = '{}'.format(value[4])
    direction_id = '{}'.format(value[5])
    block_id = '{}'.format(value[6])
    shape_id = '{}'.format(value[7])
    wheelchair_acesible = '{}'.format(value[8])
    bikes_allowed = '{}'.format(value[9])

    trip_line = '{},{},{},{},{},{},{},{},{},{}'.format(route_id, service_id, trip_id, trip_headsign,
                                                       trip_short_name, direction_id, block_id, shape_id,
                                                       wheelchair_acesible, bikes_allowed)
    print(colored(trip_line, color='green', on_color='on_white'))

    if not route_id and not service_id and not trip_id:
    # If any required value is empty write exception and continue loop
        exception = 'Required value missing. trip line i:{} route_id:{} service_id:{} trip_id:{}'.format(i, route_id, service_id, trip_id)
        write_exception_file(exception, workbook, worksheet, configs)

    # Can't write trips header for each trip.
    # worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)
    worksheet_name_output_dir = worksheet_title

    # Open and append to  existing file
    gtfs_file = os.path.join(worksheet_name_output_dir, 'trips.txt')
    f = open(gtfs_file, "a+")
    f.write('{}\n'.format(trip_line))
    f.close()

    # c_trip_line = colored(trip_line,color='green', on_color='on_white')
    # print('write_trips_file trip_line:{}'.format(c_trip_line))
    print('Writing trip {}... to {}'.format(trip_id, gtfs_file))


def write_stops_file(worksheet_title, rows, workbook, worksheet, configs):
    """
    GTFS stops.txt file from worksheet output in csv format with key values:
    stop_id,stop_code,stop_name,stop_desc,stop_lat,stop_lon,zone_id,stop_url,location_type,parent_station,
    stop_timezone,wheelchair_boarding

    :param worksheet_title: Google Sheets worksheet name
    :param configs: configuration file values
    :param worksheet:
    :return None
    """
    # Keep a stops list of all stops in memory for stop_times stop_id check.
    stop_list = []

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)

    # File header
    x = GtfsHeader()
    x.write_header('stops', worksheet_name_output_dir)

    # Iterate across the valid rows. The worksheet data has 4 [rows] of static data.
    stop_list = []
    for i in range(3, len(rows)):

        # Required. Something must exist in the worksheet row to have been flagged.
        # Check to ensure a valid stop; must have stop_id, stop_name, stop_lat, stop_lon
        try:
            # Required
            stop_id     = worksheet[i][3]
            stop_name   = worksheet[i][11]
            stop_lat    = worksheet[i][13]
            stop_lon    = worksheet[i][14]
            # Optional
            stop_code   = worksheet[i][10]
            stop_desc   = worksheet[i][12]
            zone_id     = worksheet[i][15]
            stop_url    = worksheet[i][16]
            loc_type    = worksheet[i][17]
            parent      = worksheet[i][18]
            timezone    = worksheet[i][19]
            wheel_board = worksheet[i][20]

        except IndexError:
            # Catch Out of Range error and write exception
            exception = 'IndexError. stop row i:{}'.format(i)
            write_exception_file(exception, workbook, worksheet_title, configs)
            print(colored(exception, color='red'))
            continue

        if stop_id and stop_name and stop_lat and stop_lon: # all required fields?
            # Format stop line output
            stop = ('{},{},{},{},{},{},{},{},{},{},{},{}'.format(stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon, zone_id, stop_url, loc_type, parent, timezone, wheel_board))

            # Check to see if stop exists, write to exception if true.
            if stop[0] in stop_list:
                exception = 'Duplicate stop row {} :{}'.format(i, stop)
                write_exception_file(exception, workbook, worksheet_title, configs)
                print(colored(exception))
            # Write to stop_list if it does not exist. Print the stop to console.
            else:
                stop_list.append(stop)
                print(colored('writing_stop --> stop_line:{}'.format(stop), color='blue', on_color='on_white'))
        else:
            # If any required value is empty write exception and continue loop
            exception = 'Required value missing. stop line i:{} stop_id:{} stop_name:{} stop_lat:{} stop_lon{}'.format(i, stop_id, stop_name, stop_lat, stop_lon)
            write_exception_file(exception, workbook, worksheet_title, configs)

    # Write stop_list to stops.txt
    gtfs_file = os.path.join(worksheet_name_output_dir, 'stops.txt')
    f = open(gtfs_file, "a+")
    for stop in stop_list:
        f.write('{}\n'.format(stop))
    f.close()

    return stop_list


def write_calendar_file(worksheet_title, workbook, worksheet, configs):
    '''
    Write a service calendar derived from the worksheet entries.
        Creates a service exception for the calendar service_id for each Holiday specified in the Config file.

    :param worksheet_title: Used to generate complete path to worksheet feed file.
    :param worksheet: Read the service_id and service DOW. Service dates are ignored as they are read from the Config.
    :param configs:
    :return:
    '''

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)

    # File header
    x = GtfsHeader()
    x.write_header('calendar', worksheet_name_output_dir)

    # REMEMBER Python counts begin at zero!
    # Worksheet data is in the third row; retrieved as the second list of row data.
    # Address the nested list-static data as list[1] (second list)
    try:
        service_id  = worksheet[1][28]
        monday      = worksheet[1][29]
        tuesday     = worksheet[1][30]
        wednesday   = worksheet[1][31]
        thursday    = worksheet[1][32]
        friday      = worksheet[1][33]
        saturday    = worksheet[1][34]
        sunday      = worksheet[1][35]
    except IndexError: # Out of bounds if there is no worksheet to process
        exception = 'Is there a worksheet referenced in calendar?.'
        write_exception_file(exception, workbook, worksheet_title, configs)

    # Placeholders for feed dates in spreadsheet are ignored.
    if configs.feed_start_date:
        start_date  = configs.feed_start_date
    else:
        # TODO Coordinate this start date with GtfsCalendar start date.
        start_date = pd.datetime.today().strftime('%Y%m%d')

    end_date    = configs.feed_end_date

    calendar_info = '{},{},{},{},{},{},{},{},{},{}\n'.format(service_id, monday, tuesday,
                                                             wednesday, thursday, friday, saturday, sunday,
                                                             start_date, end_date)

    if not service_id and not monday and not tuesday and not wednesday and not thursday and not friday and not saturday and not sunday:
        # If any required value is empty write exception and continue loop
        exception = 'Required value missing in calendar.'
        write_exception_file(exception, workbook, worksheet_title, configs)

    # Open and append to existing file
    gtfs_file = os.path.join(worksheet_name_output_dir, 'calendar.txt')
    f = open(gtfs_file, "a+")
    f.write('{}'.format(calendar_info))
    f.close()

    print('Writing calendar.txt to {}'.format(gtfs_file))


def write_calendar_dates_file(service_id, worksheet_title, configs):
    '''
    This function is called at the end of the write_calendar function, as the service_id required for
        the calendar_dates output is generated from the worksheet entries.
        Duplicates are stripped out of the feed later.
    :param service_id: Service ID is the name of the servcie (e.g., weekday, saturday) from the worksheet
    :param worksheet_title: The worksheet title is also the folder name of the feed file location for the trip.
    :param configs: The configs object containing a holiday list and output locations
    :return:
    '''

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)

    # File header
    x = GtfsHeader()
    x.write_header('calendar_dates', worksheet_name_output_dir)
    exception_type = '2'

    # Display expected and received holidays to aid troubleshooting
    print('There are {} holidays in configs.'.format(len(configs.holidays.split(','))))

    dates = ServiceExceptions(configs)

    # Display return values
    if len(dates) != len(configs.holidays.split(',')):
        print(colored('Expected {} days, recieved {} days.'.format(len(configs.holidays.split(',')), len(dates)), color='red'))
    else:
        print('Returned formatted dates:{}'.format(dates))

    # Setup a line entry for each holiday
    # Open and append date to existing file
    gtfs_file = os.path.join(worksheet_name_output_dir, 'calendar_dates.txt')
    f = open(gtfs_file, "a+")
    for ex_day in dates:
        calendar_dates_info = '{},{},{}\n'.format(service_id, ex_day, exception_type)
        f.write('{}'.format(calendar_dates_info))
    f.close()

    print('Writing calendar_dates.txt to:{}...'.format(gtfs_file))


def write_routes_file(worksheet_title, worksheet, configs):
    """

    :param worksheet:
    :return:
    """

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)

    x = GtfsHeader()
    # File header
    x.write_header('routes', worksheet_name_output_dir)

    # Worksheet data is in the third row; retrieved as the second list of row data, first when count from zero.
    # Address the nested list-static data as list[1] (second list)

    route_id            = worksheet[1][10]
    agency_id           = configs.agency_id
    route_short_name    = worksheet[1][11]
    route_long_name     = worksheet[1][12]
    route_desc          = worksheet[1][13]
    if  worksheet[1][14]:
        route_type      = worksheet[1][14]
    else:
        route_type      = '3'
    route_url           = worksheet[1][15]
    route_color         = worksheet[1][16]
    route_text_color    = worksheet[1][17]

    route_info = '{},{},{},{},{},{},{},{},{}\n'.format(route_id, agency_id, route_short_name,
                                                       route_long_name, route_desc, route_type, route_url, route_color,
                                                       route_text_color)

    # Open and append to existing file
    gtfs_file = os.path.join(worksheet_name_output_dir, 'routes.txt')
    f = open(gtfs_file, "a+")
    f.write('{}'.format(route_info))
    print('Writing routes.txt to {}'.format(gtfs_file))
    f.close()


def write_feed_info_file(worksheet_title, configs):

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)

    # File header
    x = GtfsHeader()
    x.write_header('feed_info', worksheet_name_output_dir)

    if not configs.feed_start_date:
        start_date = pd.to_datetime('today')
    else:
        start_date = pd.to_datetime(configs.feed_start_date)
    if pd.Timestamp(configs.feed_end_date) > (pd.Timestamp(start_date) + pd.DateOffset(days=int(configs.delta_max))):
        end_date = pd.Timestamp(start_date) + pd.DateOffset(configs.delta_max)
    else:
        end_date = pd.Timestamp(configs.feed_end_date)
    start_date  = start_date.strftime('%Y%m%d')
    end_date    = end_date.strftime('%Y%m%d')

    feed_info = '{},{},{},{},{},{}\n'.format(configs.feed_publisher_name, configs.feed_publisher_url, configs.feed_lang,
                                             start_date, end_date, configs.feed_version)

    print('Writting feed_info.txt to {}'.format(worksheet_name_output_dir))

    # Open and overwrite existing file
    gtfs_file = os.path.join(worksheet_name_output_dir, 'feed_info.txt')
    f = open(gtfs_file, "a+")
    f.write('{}'.format(feed_info))
    f.close()


def write_agency_file(worksheet_title, configs):
    '''
    Write agency.txt from values in configuration file.

    :param worksheet_title: present worksheet name. If none then the 'master' GTFS feed.
    :param configs: arguments from the configuration file.
    :return:
    '''

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)

    # Overwrite with file header
    x = GtfsHeader()
    x.write_header('agency', worksheet_name_output_dir)

    # Agency.txt information
    print('Writing agency.txt to {}'.format(worksheet_name_output_dir))
    agency_info = '{},{},{},{},{},{}'.format(str(configs.agency_id), str(configs.agency_name), str(configs.agency_url),
                                             str(configs.agency_timezone), str(configs.agency_lang), str(configs.agency_phone))


    # Write info line to file
    f = open(os.path.join(worksheet_name_output_dir,'agency.txt'), "a+")
    f.write('{}\n'.format(agency_info))
    f.close()


def write_fare_rules_file(worksheet_title, configs):
    '''
    Incomplete; writes the required fare_id.
    fare_id(r),route_id(o),origin_id(o),destination_id(o),contains_id(o)

    :param worksheet_title:
    :param configs:
    :return:
    '''

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)

    # File header
    x = GtfsHeader()
    x.write_header('fare_rules', worksheet_name_output_dir)

    # Fare_rules are in the configuration file. Make config string into list.
    fare_ids        = configs.fare_ids.split(',')
    route_ids       = ''
    origin_ids      = ''
    destination_ids = ''
    contains_ids    = ''
    # Construct line info
    for i in range(len(fare_ids)):
        line = '{},{},{},{},{}\n'.format(fare_ids[i], route_ids, origin_ids, destination_ids, contains_ids)

        # Append info existing file
        gtfs_file = os.path.join(worksheet_name_output_dir, 'fare_rules.txt')
        f = open(gtfs_file, "a+")
        f.write('{}'.format(line))
    f.close()


def write_fare_attributes_file(worksheet_title, configs):
    '''
    Write fare_attributes.txt from values in configuration file.

    fare_id(r),price(r),currency_type(r),payment_method(r),transfers(r),transfer_duration(O)

    :param worksheet_title: present worksheet name. If none then the 'master' GTFS feed.
    :param configs: arguments from the configuration file.
    :return:
    '''

    # Setup output file location
    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)

    # Overwrite with file header
    x = GtfsHeader()
    x.write_header('fare_attributes', worksheet_name_output_dir)

    # Fare_rules are in the configuration file. Make config string into list.
    fare_ids = configs.fare_ids.split(',')
    prices  = configs.prices.split(',')
    transfers = configs.transfers.split(',')
    durations = configs.durations.split(',')
    # Construct line info
    for i in range(len(fare_ids)):
        line = '{},{},{},{},{},{}\n'.format(fare_ids[i], prices[i], configs.currency, configs.payment_method, transfers[i], durations[i])
        # Write info line to file
        gtfs_file = os.path.join(worksheet_name_output_dir, 'fare_attributes.txt')
        f = open(gtfs_file, "a+")
        f.write('{}'.format(line))
    f.close()


def create_exceptions_file(configs):

    exception_file = os.path.join(os.path.expanduser(configs.report_path), 'exceptions.txt')
    # Overwrite existing file
    f = open(exception_file, "w")
    f.write('GTFS Generator Process start:{}\n'.format(pd.to_datetime('now').strftime("%c")))
    f.close()


def write_exception_file(exception, workbook, worksheet, configs):

    # TODO Delete this
    # worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)

    exception_file = os.path.join(os.path.expanduser(configs.report_path), 'exceptions.txt')

    # Open and append existing file (clear the file before opening the worksheet)
    f = open(exception_file, "a")
    now = pd.to_datetime('now').strftime("%c")
    f.write('Workbook: {} Worksheet:{}\n   exception:{}  {} '.format(workbook, worksheet, exception, now))
    f.close()


def get_root_from_kml(kmlFile):

    tree = ET.parse(kmlFile)
    root = tree.getroot()

    return root


def get_name_elements_from_root(root):
    namespace = '{http://www.opengis.net/kml/2.2}'
    allNameElements = root.findall('{0}Document/{0}Folder/{0}name'.format(namespace))

    if allNameElements:
        return allNameElements
    else:
        allNameElements = root.findall('{0}Document/{0}name'.format(namespace))
        return allNameElements


def get_kml_elements(kml_file):

    root = get_root_from_kml(kml_file)
    allNameElements = get_name_elements_from_root(root)
    allCoordsElements = get_coords_elements_from_root(root)

    return allNameElements, allCoordsElements


def get_coords_elements_from_root(root):

    namespace = '{http://www.opengis.net/kml/2.2}'

    allCoordsElements = root.findall(
        '{0}Document/{0}Folder/{0}Placemark/{0}LineString/{0}coordinates'.format(namespace))

    if allCoordsElements:
        return allCoordsElements
    else:
        allCoordsElements = root.findall('{0}Document/{0}Placemark/{0}LineString/{0}coordinates'.format(namespace))
        return allCoordsElements


def write_shapes_header(worksheet_title, configs):

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)

    # File header
    x = GtfsHeader()
    x.write_header('shapes', worksheet_name_output_dir)


def write_shape_from_kml(shapeID, workbook, title, configs):
    """
    Function constructs a .kml and .txt filename from the worksheet entry.
    If the kml_txt exists, then the text file contains two or more kml entries to be concatenated together into
       a GTFS shapes.txt file.
    If the kml_txt does not exist, then the kml_file is processed as a singlton into a GTFS shapes.txt file.
    :param shapeID: The shapeID from worksheet. No extension!
    :param title: The spreadsheet title.
    :param configs: The configuration file object.
    :return:
    """

    tripKML = '{}.kml'.format(shapeID)
    tripKML_loc = os.path.join(os.path.expanduser(configs.kml_files_root), tripKML)
    tripKML_txt_file = '{}.txt'.format(shapeID)
    tripKML_txt_loc = os.path.join(os.path.expanduser(configs.kml_files_root), tripKML_txt_file)

    print('  Looking for KML file or list: {} from worksheet:{} in path\n   KML {}\n   TXT {}'.format(shapeID, title, tripKML_loc, tripKML_txt_loc))

    worksheet_name = title

    shapetxt_out = os.path.join(os.path.expanduser(configs.gtfs_path_root), worksheet_name, 'shapes.txt')
    print('  shapes.txt output to:{}'.format(shapetxt_out))

    # Single KML file processing.
    if os.path.isfile(tripKML_loc):

        print(colored('  Found KML:{} in directory: {}'.format(tripKML, configs.kml_files_root), color='blue'))

        last_sequence_number = 0
        accumulated_distance = 0.0
        allNameElements, allCoordsElements = get_kml_elements(tripKML_loc)
        write_coords_to_file(shapetxt_out, allNameElements, allCoordsElements, shapeID, last_sequence_number,
                             accumulated_distance, configs)

    # Multiple KML file processing. Read KML filenames from a text file with the name of the shapeID.
    elif os.path.isfile(tripKML_txt_loc):

        print(colored('  Found TXT: {} in directory: {}'.format(tripKML_txt_loc, configs.kml_files_root), color='green'))

        print('  tripKML_list file name:{}'.format(tripKML_txt_file))

        with open(tripKML_txt_loc, 'r') as kml_list:
            kml_filenames = kml_list.readlines()
            kml_files = []
            for elem in kml_filenames:
                kml_files.append(elem.strip())
            print('   KML files in {}:{}'.format(tripKML_txt_file,kml_files))
            last_sequence_number = 0
            accumulated_distance = 0.0

            for item in kml_files:
                print('    processing KML file:{}'.format(item))
                tripKML_loc = os.path.join(os.path.expanduser(configs.kml_files_root), item)
                allNameElements, allCoordsElements = get_kml_elements(tripKML_loc)
                last_sequence_number, accumulated_distance = write_coords_to_file(shapetxt_out, allNameElements, allCoordsElements, shapeID, last_sequence_number, accumulated_distance, configs)
    # No KML or TXT files found
    else:
        print(colored('  KML nor TXT: {} found in directory: {}'.format(tripKML, configs.kml_files_root), 'red'))
        exception = 'KML or TXT not found in\n   {}.'.format(configs.kml_files_root)
        worksheet = title
        write_exception_file(exception, workbook, worksheet, configs)


def get_vincenty_distance(point1, point2, configs):
    """
    Determine the distance between two coordinate pairs.
    :param point1: Latitude, Longitude pair 1
    :param point2: Latitude, Longitude pair 2
    :param configs: Configuration file values, distance units in feet, miles, meters, or kilometers. No value defaults to miles.
    :return:
    """
    # Calculate the distance between to lat/long pairs
    if configs.dist_units == 'feet':
        d = vincenty(point1, point2).feet
    elif configs.dist_units == 'miles':
        d = vincenty(point1, point2).miles
    elif configs.dist_units == 'meters':
        d = vincenty(point1, point2).meters
    elif configs.dist_units == 'kilometers':
        d = vincenty(point1, point2).kilometers
    else:
        d = vincenty(point1, point2).miles
    return d


def write_shape_line(shape_txt_out, shapeID, lat2, lng2, last_sequence_number, accumulated_distance):
    """

    :param shape_txt_out:
    :param shapeID:
    :param lat2:
    :param lng2:
    :param last_sequence_number:
    :param accumulated_distance:
    :return:
    """
    # Write each output line in shapes.txt
    f = open(shape_txt_out, 'a')
    # Removed distance to previous point.
    line_out = "{}, {:.6f}, {:.6f}, {}, {:.2f}\n".format \
        (shapeID, lat2, lng2, last_sequence_number, accumulated_distance)
    # print(' shape_txt_out:{}'.format(shape_txt_out))
    # print('  write_shape_line:{}'.format(line_out))
    f.write(line_out)


def write_coords_to_file(shape_txt_out, allNameElements, allCoordsElements, shapeID, last_sequence_number, accumulated_distance, configs):
    # Write the KML line coordinate pairs, sequence number, distance, accumulated distance
    lat1 = 0.0
    lng1 = 0.0
    for nameElement in allNameElements:
        # For all the coordinates in the kml line element
        # For the ith coordinate row
        for i in allCoordsElements:
            # For the jth column in the ith line (lines separated by a blank)
            for j in i.text.split(' '):
                for k in enumerate(j.split(',')):
                    if (k[0] == 0):
                        # First column is the longitude
                        lng2 = float(k[1])
                    elif k[0] == 1:
                        # Second column is the latitude
                        lat2 = float(k[1])
                if lat1 == 0 and lng1 == 0:
                    distance = 0.0
                else:
                    # distance = getHaversine((lat1, lng1), (lat2, lng2))
                    point1 = (lat1, lng1)
                    point2 = (lat2, lng2)
                    distance = get_vincenty_distance(point1, point2, configs)

                # Accumulate sequence number
                last_sequence_number += 1

                # Accumulate shape distances
                accumulated_distance = distance + accumulated_distance

                # Write the line to the shapes.txt file
                write_shape_line(shape_txt_out, shapeID, lat2, lng2, last_sequence_number, accumulated_distance)
                # write_shape_line(shape_txt_out, shapeID, lat2, lng2, last_sequence_number, accumulated_distance, distance)

                # Assign coordinates to previous
                lat1 = lat2
                lng1 = lng2

    print(colored('  KML as shape.txt for {}, distance:{:.3f} {} nodes:{}'.format(shapeID, accumulated_distance, configs.dist_units, last_sequence_number), 'green', attrs=['bold']))

    return last_sequence_number, accumulated_distance


def create_gtfs_zip(output_path, out_filename):

    # http://effbot.org/librarybook/zipfile.htm
    zfile = zipfile.ZipFile("{}/{}.zip".format(output_path, out_filename), "w")

    # Use glob to expand the *.txt term.
    for name in glob.glob("{}/*.txt".format(output_path)):
        zfile.write(name, os.path.basename(name), zipfile.ZIP_DEFLATED)

    zfile.close()

    # print('{}\n',zipfile.ZipFile.infolist(zfile))
    zip_file_names = zipfile.ZipFile.namelist(zfile)
    for out_filename in zip_file_names:
        print('   {}'.format(out_filename))


def run_validator(folder_path, filename, configs):
    '''
    Run feedvalidator.py (Python 2.5) against each worksheet's GTFS feed.

    :param folder_path: subfolder with worksheet gtfs files
    :param filename: name of the worksheet zip file = worksheet title or combined feed filename
    :param configs: arguments from the configuration file
    :return:
    '''

    gtfs_zip    = os.path.join(os.path.expanduser(configs.gtfs_path_root), folder_path, filename + '.zip')
    print('folder path:{}\n filename:{}\n  gtfs_zip:{}'.format(folder_path, filename, gtfs_zip))
    os.chdir(os.path.join(expanduser(configs.gtfs_path_root), folder_path))

    # ref: https://github.com/google/transitfeed/wiki/FeedValidator
    note = subprocess.run(['feedvalidator.py','-n','-o','{}'.format('validator.html'), '{}'.format(gtfs_zip)])
    print(colored('{} Feed Validator Result {}'.format(15 * '^', 15 * '^'), 'cyan', 'on_grey'))
    # TODO Return results from stdout
    #ref: http://stackoverflow.com/questions/5136611/capture-stdout-from-a-script-in-python


def get_google_worksheet_row_col_list(column_list, worksheet, configs):

    '''
    Retrieve worksheet dimensions defined by a row and column list
    :param column_list:
    :param worksheet:
    :param configs:
    :return:
    '''

    # Determine the size of the worksheet
    last_cell = worksheet.get_addr_int(worksheet.row_count, worksheet.col_count)

    # Define the section of the spreadsheet that contains the stop times and stop_ids.
    stop_time_section = worksheet.range('AB7:' + last_cell)
    stop_idx_begin = 'D' + str(configs.row_idx)
    stop_idx_end = 'D' + str(worksheet.row_count)
    stops_section_range = '{}:{}'.format(stop_idx_begin, stop_idx_end)
    stops_section = worksheet.range(stops_section_range)


    # Determine the rows and columns to iterate across.
    row_list = []
    # Accumulate a list of  all the row numbers with a stop_id value, (including stations).
    for cell in stops_section:
        # Cell is not empty in the stop_section_range. Any value will count row. Check for valid stop before writing.
        if (cell.value):
            row_list.append(int(cell.row))
    # Unique values define a set. This strips any duplicates.
    row_list = set(row_list)
    # Cast the set back to a list
    row_list = list(row_list)
    # Sort list
    row_list.sort()

    for cell in stop_time_section:
        if (cell.value):
            # Accumulate a list of all the column numbers with a time.
            column_list.append(int(cell.col))
    # Unique values in a set
    column_list = set(column_list)
    # Set back to list
    column_list = list(column_list)
    # Sort list
    column_list.sort()

    return row_list, column_list


def get_excel_worksheet_row_col_list(column_list, worksheet, configs):
    """

    :param column_list:
    :param worksheet:
    :param configs:
    :return:
    """


def get_google_worksheet_data(row_list, worksheet):
    # Row Value list
    worksheet_data = []

    # Add all the row values with data from the G_worksheet to worksheet_data list
    for row in row_list:
        worksheet_data.append(worksheet.row_values(row))

    return worksheet_data


def get_excel_worksheet_data(row_list, worksheet):
    """

    :param row_list:
    :param worksheet:
    :return:
    """

    # Row Value list
    worksheet_data = []

    # Add all the row values with data from the G_worksheet to worksheet_data list
    for row in row_list:
        worksheet_data.append(worksheet.row_values(row))

    return worksheet_data


def print_worksheet_data(ws_data):
    for row in range(0, len(ws_data)):
        print('{}'.format(ws_data[row]))


def write_worksheet_data_to_csv(current_worksheet_title, ws_data, configs):

    worksheet_name_output_dir = get_worksheet_name_output_dir(current_worksheet_title, configs)

    data_file = os.path.join(worksheet_name_output_dir, 'data.csv')

    # Open and overwrite existing file
    f = open(data_file, "w+")

    for row in range(0, len(ws_data)):
        f.write('{}\n'.format(ws_data[row]))

    f.close()


def clear_run_info_file(note, configs):
    """
    Clear existing run info file, write date and time.
    :param title:
    :param note:
    :return:
    """
    print('Clear run_info\n filename:{}\n Date and time:{}'.format\
              (os.path.join(configs.report_path, configs.stats_filename), pd.to_datetime('now').strftime('%c')))
    # If the report location does not exist, create it.
    if  not os.path.exists(os.path.expanduser(configs.report_path)):
        print(colored('{} does not exist, creating {}'.format\
                          (os.path.expanduser(configs.report_path), \
                           os.path.join(os.path.expanduser(configs.report_path), configs.stats_filename)), 'red'))
        # make directory from full path in config file
        os.makedirs(os.path.expanduser(configs.report_path))
    f = open(os.path.join(os.path.expanduser(configs.report_path), configs.stats_filename), 'w')
    f.write('{}\n   {}'.format(pd.to_datetime('now').strftime("%c"), note))


def write_run_info_to_file(elapsed_time, title, note, configs):
    """
    Write run info to file.
    :param start_time:
    :param stop_time:
    :param title:
    :param note:
    :return:
    """
    # Open and append to  existing file
    ts = pd.to_datetime('now').tz_localize('utc')
    local_time = ts.tz_convert(configs.local_tz)
    print('from write_run_info_to_file\n filename:{}\n et:{} seconds'.format\
              (os.path.join(configs.report_path, configs.stats_filename), elapsed_time))
    if  not os.path.exists(os.path.expanduser(configs.report_path)):
        print(colored('{} does not exist, creating {}'.format(os.path.expanduser(configs.report_path), \
                           os.path.join(os.path.expanduser(configs.report_path), configs.stats_filename)), 'red'))
        # make directory from full path in config file
        os.makedirs(os.path.expanduser(configs.report_path))
    f = open(os.path.join(os.path.expanduser(configs.report_path), configs.stats_filename), 'a')
    f.write('{} {} et:{} seconds ts:{}\n'.format(title, note, elapsed_time, local_time.strftime('%X')))
    f.close()


def read_worksheet_data_from_csv(current_worksheet_title, configs):
    # TODO read_worksheet_data_from_csv not tested. Pickle the output?
    worksheet_name_output_dir = get_worksheet_name_output_dir(current_worksheet_title, configs)
    data_file = os.path.join(worksheet_name_output_dir, 'data.csv')
    # Open and read csv dump from 'write_worksheet_data_to_csv'
    with open(data_file, newline='') as csvfile:
        sheet_reader = csv.reader(csvfile, delimiter=',')
        for row in sheet_reader:
            print(','.join(row))


def print_et (text_color, start_time, title, note, configs):

    stop_time = datetime.now()
    tdelta = stop_time - start_time
    tdelta = tdelta.seconds
    tdelta_colored = colored(tdelta, text_color, 'on_grey')
    c_note = colored(note, text_color)
    print('   Elapsed Time: {} seconds. {} time stamp {}'.format(tdelta_colored, c_note, stop_time.strftime('%c')))
    write_run_info_to_file(tdelta, title, note, configs)


def combine_gtfs_feeds(worksheets, configs):
    '''
        Combine feed files from each worksheet process.
    1. Identical feed files that require no action:
        a. agency.txt (from config)
        b. feed_info.txt (from config)
        d. fare_attribute (from config)
        e. fare_rules (from config)
    2. Feed files that require only concatenation of lines:
        a. trips.txt
        b. stop_times.txt
        c. shapes.txt
    3. Feed files that require search / add if absent:
        a. stops.txt
        b. calendar.txt
        c. calendar_dates.txt
        c. routes.txt

    :param worksheets: list of worksheets previously processed
    :param configs: arguments from the configuration file
    :return:
    '''

    print('Starting merge...')

    # Delete any existing master GTFS files
    delete_master(configs)
    # Combine the worksheets, eliminating duplicate lines
    combine_files(worksheets, configs)
    # Zip the master files together
    agency_ID = configs.agency_id
    # TODO use set to eliminate duplicate stops
    create_gtfs_zip(os.path.expanduser(configs.gtfs_path_root), agency_ID)
    # Validate the master
    path = os.path.expanduser(configs.gtfs_path_root)
    filename = configs.agency_id
    run_validator(path, filename, configs)


def combine_files(worksheets, configs):
    '''
    Combine individual GTFS files gnerated from worksheets.
        module 'fileinput'
    :param worksheets: List of processed worksheets
    :return:
    '''

    gtfs_filelist = ['agency','calendar','calendar_dates','fare_attributes','fare_rules','feed_info','routes','shapes',
                 'stop_times','stops','trips']

    # print('combine_files {} in worksheets {}'.format(gtfs_filelist, worksheets))

    for gtfs_file in gtfs_filelist:

        # ref:http://stackoverflow.com/questions/13613336/python-concatenate-text-files
        outfilename_tmp = os.path.join(os.path.expanduser(configs.gtfs_path_root), gtfs_file + '.tmp')
        outfilename = os.path.join(os.path.expanduser(configs.gtfs_path_root), gtfs_file + '.txt')

        # Combine gtfs_files for all worksheets
        for worksheet in worksheets:
            worksheet_name_input_dir = get_worksheet_name_output_dir(worksheet, configs)
            infilename = os.path.join(worksheet_name_input_dir, gtfs_file + '.txt')

            # Combine lines in fin and fout
            with open(outfilename_tmp, 'a') as fout, fileinput.input(infilename) as fin:
                for line in fin:
                    fout.write(line)
                fout.close()

        # ref: http://stackoverflow.com/questions/1215208/how-might-i-remove-duplicate-lines-from-a-file
        lines_seen = set() # holds lines already seen
        # Append lines to  master file.
        fout = open(outfilename, "a")
        infilename_tmp = outfilename_tmp

        # print('combine_files set lines --> infile:{} outfile:{}'.format(infilename_tmp,outfilename))

        for line in open(infilename_tmp, "r"):
            if line not in lines_seen: # not a duplicate
                fout.write(line)
                lines_seen.add(line)
        fout.close()
        os.remove(infilename_tmp)


def delete_master(configs):
    '''

    :param configs:
    :return:
    '''

    gtfs_filelist = ['agency','calendar','calendar_dates','fare_attributes','fare_rules','feed_info','routes','shapes',
                     'stop_times','stops','trips']

    for file in gtfs_filelist:
        masterfiles = os.path.join(os.path.expanduser(configs.gtfs_path_root), (file + '.txt'))

        try:

            print('delete_master deleting {}'.format(masterfiles))

            os.remove(masterfiles)
        except FileNotFoundError:
            pass


def run_schedule_viewer(configs):
    '''
    Run the Google schedule viewer from the transit feedValidator module.
    :param configs: Arguments from the configuration file
    :return:
    '''
    gtfs_zip  = os.path.join(os.path.expanduser(configs.gtfs_path_root), configs.agency_id + '.zip')
    print('GTFS_zip:{}'.format(gtfs_zip))
    # ref: https://github.com/google/transitfeed/wiki/FeedValidator
    subprocess.run(['schedule_viewer.py','{}'.format(gtfs_zip)])


def google_worksheets_by_workbook_to_dict(configs, defaults):
    # Assemble a dictionary of workbooks and worksheets for a report.
    workbooks = configs.google_workbook_names.split(',')
    worksheet_dict = {}
    for workbook in workbooks:
        route_workbook = open_google_workbook(workbook, defaults, configs)
        worksheets = route_workbook.worksheets()
        for worksheet in worksheets:
            worksheet_dict.setdefault(workbook, []).append(worksheet.title)
    return worksheet_dict


def write_workbook_dictionary(workbook_dictionary, configs):
    f = open(os.path.join(os.path.expanduser(configs.report_path), configs.worksheet_list), 'w')
    print('The {} route set has {} workbooks.'.format(configs.agency_id.upper(), len(workbook_dictionary)))
    f.write('The {} route set has {} workbooks.'.format(configs.agency_id.upper(), len(workbook_dictionary.keys())))
    f.write(' >> ignoring sheets:{}'.format(configs.ignore_sheets))
    for key, value in workbook_dictionary.items():
        # print('\nWorkbook {} has {} worksheets:'.format(key, len(workbook_dictionary[key])))
        f.write('\nWorkbook {} has {} worksheets.\n'.format(key, len(workbook_dictionary[key])))
        # print('{}'.format(value))
        f.write('{}'.format(value))
    f.close()


def copy_file(start_time, configs):
    """
    Copy completed zipped feed file to location in configuration file.
    :param configs: agency_id, gtfs_path_root, copy_path
    :return:
    """
    gtfs_source = os.path.join(os.path.expanduser(configs.gtfs_path_root), configs.agency_id + '.zip')
    gtfs_destination = os.path.join(os.path.expanduser(configs.copy_path), configs.agency_id + '.zip')

    # copyfile source, destination
    print('Source:{}\n  Destination:{}'.format(gtfs_source, gtfs_destination))
    copyfile(gtfs_source, gtfs_destination)
    note = 'Validation results'
    print_et(text_color='green', start_time=start_time, title='  >> Copying file to feed pickup.'.format('copy file'),
             note=note, configs=configs)


def remove_dup_stops(stops):
    """
    Remove duplicate stops from a stops.txt file
    :param stops:
    :return:
    """
    # List to set
    stop_set = set(stops)
    sorted(stop_set)
    list(stop_set)

    # Could use .add for iterables.
    # stop_set = set()
    # for stop in stops:
    #     stop_set.add(stop)


def read_stops(configs):
    """
    Read a GTFS stops.txt to a list.
    :param stops_file:
    :return:
    """
    stops_file = os.path.join(os.path.expanduser(configs.gtfs_path_root),'stops.txt')
    with open(stops_file, 'r') as f:
        reader = csv.reader(f)
        stops = list(reader)
        return stops


def main (argv=None):
    # Display the the system path, Python version, and platform that is running.
    print(sys.path)
    print('Python {} on {}'.format(sys.version, sys.platform))
    print('Hex version is: {}'.format(sys.hexversion))


    # Ref: http://stackoverflow.com/questions/3609852/which-is-the-best-way-to-allow-configuration-options-be
    # -overridden-at-the-comman

    # Do argv default this way, as doing it in the functional
    # declaration sets it at compile time.

    if sys.argv is None:
        argv = sys.argv

    # Parse any conf_file specification
    # We make this parser with add_help=False so that
    # it doesn't parse -h and print help.

    config_parser_for_passed_in_config_file = get_config_parser_for_passed_in_config_file()
    configs, remaining_argv = config_parser_for_passed_in_config_file.parse_known_args()

    # gettting the defaults

    defaults = Configuration(configs.config_file).get_defaults()

    # print('defaults:{}'.format(defaults))

    # Parse rest of arguments
    # Don't suppress add_help here so it will handle -h
    parser = argparse.ArgumentParser(
        # Inherit options from config_parser
        parents=[config_parser_for_passed_in_config_file]
    )

    if defaults is not None:

        parser.set_defaults(**defaults)
        parser.add_argument('--version', action='version', version='%(prog)s 2015.10')
        parser.add_argument('--test', action='store_true', help='test a function')
        parser.add_argument('--demo', action='store_true', help='demo a module')
        parser.add_argument('--generate', action='store_true',
                            help='generate gtfs format files from a Google spreadsheet containing'
                                 'turn-by-turn instructions.')

        configs = parser.parse_args(remaining_argv)

        pretty_print_args(configs)

        # >>> Test <<< code here
        if configs.test is True:
            print('Testing is true...\n')

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            # Call the function to test

            # Google workbook; get G_workbook names from configs and worksheets object from the G_workbook.
            start_time = pd.to_datetime('now')
            stops = read_stops(configs)
            print(stops)

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        elif configs.generate is True:

            # <<<<<<<<<< Generate Generate Generate Generate Generate >>>>>>>>>>

            start_time = datetime.now()
            print("generating...\n")
            # Google workbook; get G_workbook names from configs and worksheets object from the G_workbook.
            # List all workbooks and worksheets to text file.
            wrkbk_dict = google_worksheets_by_workbook_to_dict(configs, defaults)
            write_workbook_dictionary(wrkbk_dict, configs)

            workbooks = configs.google_workbook_names.split(',')

            # Clear existing info report, write header.
            note = ('{} Workbooks: {}.'.format(configs.agency_id.upper(), workbooks))
            clear_run_info_file(note, configs)

            for workbook in workbooks:

                # Retreive worksheets from workbook
                route_workbook = open_google_workbook(workbook, defaults, configs)
                worksheets = route_workbook.worksheets()

                # print('worksheets:{}'.format(worksheets))
                c_note = colored(note,color='green',on_color='on_grey')
                print(c_note)
                note = '{}'.format('{}\nStart processing {} workbook {} with {} worksheets.'.format( \
                    start_time, configs.agency_id, workbook, len(wrkbk_dict)))
                print_et(text_color='green', start_time=start_time, title='Workbook start.', note=note, configs=configs)
                print('Workbook:{}'.format(workbook))

                # Select the sheets to process. Create empty list to hold processed sheet titles.
                sheets  = []

                for worksheet in worksheets:
                    sheets.append(worksheet.title)
                # print('sheets:{}'.format(sheets))
                p_sheets   = []

                # Exclude worksheets named Master and Template
                ignore_list = configs.ignore_sheets.split(',')
                print('ignore list:{}'.format(ignore_list))

                # Create or overwrite exceptions.txt file in the report directory
                create_exceptions_file(configs)
                print('Creating exceptions file...')

                # Loop throught the list of worksheet titles in G_worksheets contained in the worksheets object.
                for worksheet in worksheets:
                    current_worksheet_title = worksheet.title
                    note = '{} start.'.format(worksheet)

                    # Skip the ignore list of worksheets
                    if not current_worksheet_title in ignore_list:

                        # Process the worksheet title that is in the 'sheets' list.
                        # TODO Add process_worksheet function

                        if current_worksheet_title in sheets:

                            note = '{}'.format('{}.'.format(current_worksheet_title))
                            c_note = colored(note,color='yellow',on_color='on_grey')
                            print(c_note)
                            print_et(text_color='green', start_time=start_time, title='Begin processing.', note=note, configs=configs)

                            #create_output_dir(configs)
                            create_worksheet_name_output_dir(current_worksheet_title, configs=configs)
                            print('Creating output directory...')

                            # Required rows: r2=headings(optional) r3=data r6=trip headings from configuration
                            # Cast list as integer values

                            head_data_rows = [int(s) for s in configs.head_data_rows.split(",")]

                            # Required columns: 2=stop seq 3=stopID 10-21=stop info 22-25=trip info from configuration file.
                            stops_column_list = [int(s) for s in configs.stop_data_columns.split(",")]

                            # Print the current worksheet title in color
                            current_worksheet_colored = colored(worksheet.title, 'green', 'on_grey')
                            print('{}'.format(current_worksheet_colored))

                            # TODO: Process any type of worksheet;  .xls, csv, or .ods

                            # TODO Add get_stop_times_rows as a function.
                            # Get stop_times rows.
                            note = '{}'.format('')
                            print_et(text_color='green', start_time=start_time, title='>>> Begin worksheet data retrieval. <<<', note=note,
                                     configs=configs)

                            if configs.source_type == 'google':

                                # Return a list of row numbers that contain stop data; append columns with time data
                                stop_rows, stops_column_list = get_google_worksheet_row_col_list(stops_column_list,
                                                                                                 worksheet, configs)
                                # Combine static (non-stop info) and dynamic (stop info) row numbers
                                row_list = head_data_rows + stop_rows
                                row_list.sort()

                                # Get the cell values for all rows with information from the G_worksheet.

                                ws_data = get_google_worksheet_data(row_list, worksheet)

                                ###>>  Uncomment to write retrieved worksheet data to a csv. <<###
                                # write_worksheet_data_to_csv(current_worksheet_title, ws_data, configs)


                            note = '{}'.format('')
                            print_et(text_color='green', start_time=start_time, title='Getting worksheet row data.',
                                     note=note, configs=configs)

                            # Begin writing gtfs files

                            # TODO add test for output folder

                            # Agency.txt processing
                            write_agency_file(worksheet_title=current_worksheet_title, configs=configs)

                            # Fare_attributes.txt processing. Only header at present.
                            write_fare_attributes_file(worksheet_title=current_worksheet_title, configs=configs)

                            # Fare_rules.txt processing. Only header at present.
                            write_fare_rules_file(worksheet_title=current_worksheet_title, configs=configs)

                            # Feed_info.txt processing.
                            write_feed_info_file(worksheet_title=current_worksheet_title, configs=configs)

                            # Routes.txt processing.
                            write_routes_file(worksheet_title=current_worksheet_title, worksheet=ws_data, configs=configs)

                            # Calendar.txt processing
                            write_calendar_file(worksheet_title=current_worksheet_title, workbook=workbook, worksheet=ws_data, configs=configs)

                            # Calendar_dates.txt processing
                            # TODO rework service exception determination
                            service_id = ws_data[1][28]
                            write_calendar_dates_file(service_id, worksheet_title=current_worksheet_title, configs=configs)

                            # Stops.txt processing
                            # Merge stops to stops-list.
                            stops_list = write_stops_file( worksheet_title=current_worksheet_title, rows=row_list, workbook=workbook, worksheet=ws_data, configs=configs)
                            # Remove duplicates from stops_list.
                            stops_list = remove_dup_stops(stops_list)
                            note = '{}'.format('')
                            print_et(text_color='green', start_time=start_time, title='Stops processing.', note=note,
                                     configs=configs)

                            # Trips.txt header. Trips are written from stop_times.txt processing
                            write_trips_header(worksheet_title=current_worksheet_title, configs=configs)
                            note = '{}'.format('')
                            print_et(text_color='green', start_time=start_time, title='Stop_times processing.', note=note,
                                     configs=configs)

                            # Stop times and trips processing
                            write_stop_times_file(worksheet_title=current_worksheet_title, rows=row_list, columns=stops_column_list, stops=stops_list, workbook=workbook, worksheet=ws_data, configs=configs)
                            note = '{}'.format('')
                            print_et(text_color='green', start_time=start_time, title='Shapes processing from kml.',
                                     note=note, configs=configs)

                            # Write_shapes.txt processing
                            write_shapes_header(worksheet_title=current_worksheet_title, configs=configs)
                            print('****** From main - write_shapes_header: current_worksheet_title:{}'.format(current_worksheet_title))
                            shapeID     = ws_data[1][25]
                            print('shapeID:{}'.format(shapeID))
                            write_shape_from_kml(shapeID=shapeID, workbook=workbook, title=current_worksheet_title, configs=configs)

                            print('Worksheet {} processing complete.'.format(current_worksheet_title))
                            note = '{}'.format('')
                            print_et(text_color='green', start_time=start_time, title='Worksheet {} processing complete.'.format(current_worksheet_title),
                                     note=note, configs=configs)

                            # Zip the worksheet GTFS files
                            print('Zipping GTFS.txt files...')
                            output_path = os.path.join(os.path.expanduser(configs.gtfs_path_root), current_worksheet_title)
                            out_filename = current_worksheet_title
                            create_gtfs_zip(output_path, out_filename)

                            # Run feedValidator with the worksheet's zipped GTFS files as input
                            note = '{}'.format('')
                            print_et(text_color='green', start_time=start_time, title='Validating worksheet {}.'.format(current_worksheet_title),
                                     note=note, configs=configs)
                            folder_path = current_worksheet_title
                            filename = current_worksheet_title
                            run_validator(folder_path, filename, configs)

                            note = '{}  {}  {}\n  Validation results'.format(15 * '^', current_worksheet_title, 15 * '^')

                            print_et(text_color='green', start_time=start_time, title='  >> Worksheet complete.'.format(current_worksheet_title),
                                     note=note, configs=configs)

                            # Add worksheet title to list of processed worksheets for merge function
                            p_sheets.append(current_worksheet_title)
                            # TODO write processed sheet list to file

                # Merge feeds in the processed sheets list
                print('\nCombining {} gtfs feeds from {}'.format(len(p_sheets),p_sheets))
                note = '{}'.format('')
                print_et(text_color='green', start_time=start_time, title='Combining worksheets {}.'.format(p_sheets), note=note, configs=configs)
                combine_gtfs_feeds(worksheets=p_sheets, configs=configs)

                # Run validator on combined feeds
                folder_path = ''
                filename    = configs.agency_id
                run_validator(folder_path, filename, configs)

                # Startup the schedule_viewer with the master GTFS.zip
                # run_schedule_viewer(configs)

                # Copy finished zipped gtfs to Google Drive for pickup.
                copy_file(start_time, configs)
                print_et(text_color='red', start_time=start_time, title='Finished processing.\n', note='END',
                         configs=configs)

        elif (configs.demo is True):
            print("Demo")

        else:

            print(colored("Defaults are of type None.", 'cyan'))

        return 0


if __name__ == '__main__':
    sys.exit(main())
