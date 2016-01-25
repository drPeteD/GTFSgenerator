#!/usr/bin/env python

'''
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
'''

"""
Python script to:
 1. Read a configuration file containing GTFS agency, feed_info, fare, and service exception values.
 2. Parse a series of turn-by-turn worksheets from a Google Sheets workbook
 3. Decompose KML line files representing route segments into a qualified GTFS shapes.txt entry.

    Usage: gtfsgenerator [cvtdg]
    example, generate feed files from workbook defined in the configuration file 'krt.cfg'
        gtfsgenerator -c configs/krt.cfg --generate
"""

import sys
import os
from os.path import expanduser
from termcolor import colored
from veryprettytable import VeryPrettyTable
from gtfsgenerator.Configuration import Configuration
from gtfsgenerator.Calendar import ServiceExceptions
import argparse
import csv
from datetime import datetime
from geopy.distance import vincenty
import glob
import gspread          # read Google sheets
import xml.etree.ElementTree as ET
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client import tools
import subprocess
import zipfile


# TODO Read xls sheets
# import openpyxl or xlrd    # read xls sheets
# TODO Read ods sheets
# import odsreader

class GtfsHeader:
    '''    The Header class returns the header line for the specified GTFS file.

     Attributes:
        name: gtfs file name.
        path: path to output location
        config: arguments from a configuration file
    '''

    def __init__ (self):
    # Anything to init?
        pass

    def agency(self):
        agency = 'agency_id,agency_name,agency_url,agency_timezone,agency_lang,agency_phone'
        return agency

    def calendar(self):
        calendar = 'service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date'
        return calendar

    def calendar_dates(self):
        calendar_dates = 'service_id,date,exception_type'
        return calendar_dates

    def fare_attributes(self):
        fare_attributes = 'fare_id,price,currency_type,payment_method,transfers,transfer_duration'
        return fare_attributes

    def fare_rules(self):
        fare_rules = 'fare_id,route_id,origin_id,destination_id,contains_id'
        return fare_rules

    def feed_info(self):
        feed_info       = 'feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date, feed_version'
        return feed_info

    def shapes(self):
        shapes          = 'shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence,shape_dist_traveled,dist_from_previous'
        return shapes

    def routes(self):
        routes          = 'route_id,agency_id,route_short_name,route_long_name,route_desc,route_type,route_url,route_color,route_text_color'
        return routes

    def stop_times(self):
        stop_times      = 'trip_id,arrival_time,departure_time,stop_id,stop_sequence,stop_headsign,pickup_type, drop_off_type,shape_dist_traveled'
        return stop_times

    def stops(self):
        stops = 'stop_id,stop_code,stop_name,stop_desc,stop_lat,stop_lon,zone_id,stop_url,location_type, parent_station,stop_timezone,wheelchair_boarding'
        return stops

    def trips(self):
        trips           = 'route_id,service_id,trip_id,trip_headsign,trip_short_name,direction_id,block_id,shape_id,wheelchair_accessible,bikes_allowed'
        return trips

    def write_header(self, filename, path):
        '''
        Write the GTFS header file for the specified file name (agency, shapes, routes, etc)
            to the root (+ addln folder). Overwrite existing file.
        '''

        # file header
        if filename == 'agency':
            header = self.agency()
        elif filename == 'calendar':
            header = self.calendar()
        elif filename == 'calendar_dates':
            header = self.calendar_dates()
        elif filename == 'fare_attributes':
            header = self.fare_attributes()
        elif filename == 'fare_rules':
            header = self.fare_rules()
        elif filename == 'feed_info':
            header = self.feed_info()
        elif filename == 'shapes':
            header = self.shapes()
        elif filename == 'routes':
            header = self.routes()
        elif filename == 'stop_times':
            header = self.stop_times()
        elif filename == 'stops':
            header = self.stops()
        elif filename == 'trips':
            header = self.trips()

        # Open and overwrite existing file
        #print('Header class file and path:{}'.format(path))
        f = open(path, 'w')
        f.write('{}\n'.format(header))
        f.close()


class GtfsWrite:
    '''
    Write the specified file
    '''

    def __init__(self):
        '''

        :return:
        '''
    def agency(self,header_flag,row_data,path,args):
        '''
        Write the agency.txt file data in the location specified by the path.
        :param header_flag: True=overwrite file with header. False pass the information line
        :param row_data: A line of data
        :param path: Location of agency.txt
        :param args: Not sure what is needed from args, path?
        :return:
        '''


class ServiceExceptions():
    """
    Determine and build holiday calendar.txt in YYYYMMDD format.

    """

    def __init__(self):
        """

        """
        pass

    def format_dates(self, dates, year):
        '''
        Format the days in the configuration as GTFS format YYYYMMDD.
        Days can be numeric or a limited set of holiday names.

        :param dates: holidays from config
        :param year: year to determine complete date
        :return: dates for the holidays specified as YYYYMMDD
        '''

        formatted_dates_dates = []
        for date in dates:
            if date == 'Thanksgiving DayUS':
                formatted_dates_dates.append(self.determine_thanksgiving_usa(year))
            elif date == 'New Years Day':
                formatted_dates_dates.append('{}-01-01'.format(year))
            elif date == 'Independence Day':
                formatted_dates_dates.append('{}-07-04'.format(year))
            elif date == 'Christmas Day':
                formatted_dates_dates.append('{}-12-25'.format(year))
            else:
                formatted_dates_dates.append('{}-{}'.format(year, date))

        # Print for terminal
        c_note = colored('Service exceptions for {}.'.format(year), color='green')
        print(c_note)

        # self.display_calendar_dates(formatted_dates_dates)

        # Replace the dash character with empty from each entry in the list.
        formatted_dates_dates = [day.replace('-','') for day in formatted_dates_dates]

        return formatted_dates_dates

    # def display_calendar_dates(self, dates):
    #     '''
    #     :param year: Year for the desired dates
    #     :return: calendar_dates.txt file in GTFS format
    #     Creates a calendar_dates file for the 'big four' US Holidays:
    #       New Years Day
    #       Independence Day
    #       Thanksgiving Day
    #       Christmas Day
    #     '''
    #     # Pandas is not necessary, used to display dates in a DataFrame
    #
    #     import pandas as pd
    #
    #     # Print date, holiday, and dow
    #     df = pd.DataFrame(
    #         {'Dates': dates, 'Holidays': dates})
    #     df['Dates'] = pd.to_datetime(df['Dates'])
    #     df['DOW'] = df['Dates'].dt.dayofweek
    #     days = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    #     df['DOW'] = df['DOW'].apply(lambda x: days[x])
    #     print('{}'.format(df))

    def determine_thanksgiving_usa(self, year):
        '''
        Determine the date of Thanksgiving in the USA given a year.
        Method: 1. Determine the DOW for the first of November.
                2. Apply an offset from the first day of November to the first Thursday
                3. Add 21 days to the first Thursday to determine Thanksgiving day.

        :param year: The year for the desired Thanksgiving Day.
        :return: The date of the fourth Thursday of November for the specified year.
        '''
        import datetime

        first_nov = '{}-11-01'.format(year)
        first_nov = datetime.datetime.strptime(first_nov, '%Y-%m-%d')
        pre_thurs = [6, 0, 1, 2]  # Days that Nov 1 is before the 1st Thursday
        first_nov_dow = first_nov.weekday()  # day of week: Mon=0,Th=3,Sun=6

        # Determine how many days offset from Nov 1 to the first Thursday
        if first_nov_dow in pre_thurs:
            if first_nov_dow == 6:  # Nov 1 = Sunday
                first_th_delta = 4
            else:
                first_th_delta = 3 - first_nov_dow  # Nov 1 is Mon-Wed
        else:
            first_th_delta = 3 - first_nov_dow  # Nov 1 is Fri-Sat

        # Add 21 days/3 weeks to the first Thursday of November to determine Thanksgiving Day.
        thankgiving = first_nov + datetime.timedelta(days=first_th_delta + 21)
        thankgiving = '{:%Y-%m-%d}'.format(thankgiving)  # !! leading ':' !!
        return (thankgiving)


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


def open_google_workbook(defaults, configs):
    credentials = get_credentials(client_id=defaults.get('client_id'),
                                  client_secret=defaults.get('client_secret'),
                                  client_scope=defaults.get('client_scope'),
                                  redirect_uri=defaults.get('redirect_uri'),
                                  oauth_cred_file_name=defaults.get('oauth_cred_file_name'))

    # Ref: http://www.lovholm.net/2013/11/25/work-programmatically-with-google-spreadsheets-part-2/
    gc = gspread.authorize(credentials)
    # Google workbook name is in the config file
    route_workbook = gc.open(configs.google_workbook_name)

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

    storage = Storage(os.path.join(expanduser("~"), oauth_cred_file_name))
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


def print_stops_table(stops):
    x = VeryPrettyTable()
    x.field_names = ['stop_id', 'stop_code', 'stop_name', 'stop_desc', 'stop_lat', 'stop_lon', 'zone_id', 'stop_url',
                     'location_type', 'parent_station', 'stop_timezone', 'wheelchair_boarding']
    for i in range(0, len(stops) + 1):
        x.add_row(stops[i])
    print(x)
    print('Length of stops:{}'.format(len(stops)))


def write_stop_times_file(worksheet_title, rows, columns, stops, worksheet, configs):

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)
    gtfs_file = os.path.join(worksheet_name_output_dir, 'stop_times.txt')

    # File header
    x = GtfsHeader()
    x.write_header('stop_times', gtfs_file)

    # Define the number of row and column lists.
    route_type = worksheet[1][14]
    stop_time_data = []

    # Look at the iterable row and column lists.
    # print('Stop rows:{} Time columns:{} interations:{} Route type:{}'.format(len(rows), len(columns),
    #                                                                          len(columns) * len(columns), route_type))

    # Setup write loop. Increment trip_id every iteration.
    trip_count = 0

    # TODO Add a progress bar

    # Outer loop through trips. Trip column start in 27 in worksheet, ends with column: columns[-1]

    # Length of columns comes from


    for j in range(27, int(columns[-1])):

        # Build trip_id from trip_id plus time header.
        trip_id = '{}-{}'.format(worksheet[1][20], worksheet[2][j])

        # Create a trip.txt entry
        write_trips_file(trip_id, worksheet_title=worksheet_title, worksheet=worksheet, configs=configs)

        trip_count += 1
        trip_start_check = False

        # Inner loop through stop lists (each stop row is a list inside a list)

        for i in range(3, len(rows)):

            # Departure time to empty
            departure_time = ''

            # Try if time entry exists.
            # If exist; check for time (first digit is numeric), if not, skip it.
            #      Use the first character of the time value to test.

            try:  # out of range if no loc_type AND not a time stop

                # print('Route type: {} Location type:{}'.format(route_type, loc_type))
                # print('Trip count:{} Trip start check:{} Location type:{}'.format(trip_count, trip_start_check, loc_type))

                # If stop is a station (location_type = 1) skip it. Get location type from worksheet.
                loc_type = worksheet[i][17]
                if loc_type == '1':
                    continue  # Skip the station.

                # Check to see if the first station if a time point. Flag each trip
                # The try/exception will catch no time entry.
                departure_time = worksheet[i][j]
                if trip_start_check == False:  # The first time point has not been found

                    # c_note = colored('First station is a time point; value:{}.'.format(value),color='green')
                    # print(c_note)

                    check_if_time = worksheet[i][j]
                    check_if_time = check_if_time[:1]
                    if check_if_time.isdigit():

                        # c_note = colored('First station has an arrival time and is a bus route; value:{}.'.format(value),color='green')
                        # print(c_note)
                        trip_start_check = True
                        departure_time = worksheet[i][j]
                    else:
                        # Continue to next row
                        continue
                else:  # The first time point was found. Others are time points.
                    stop_sequence = '{}'.format(worksheet[i][2])
                    stop_id = '{}'.format(worksheet[i][3])
            except IndexError:
                if trip_start_check == True:  # Keep processing if time is empty (out of range)
                    pass
                else:  # If no time in first value, next value in next row
                    continue

            # Collect all stop_time.txt values
            stop_sequence = '{}'.format(worksheet[i][2])
            stop_id = '{}'.format(worksheet[i][3])

            # If the route_type is a bus (route_type 3) then departure and arrival times are identical.
            # Not used here, but if other than a bus route - arrival != departure time.
            # route_type = worksheet[2][14]

            arrival_time = departure_time

            # Get the rest of the stop_time values. Value will be out of range if empty
            value = []
            for col in range(22, 26):
                try:
                    if worksheet[i][col] is None:
                        value.append('')
                    else:
                        value.append(worksheet[i][col])
                except IndexError:
                    value.append('')

            stop_headsign = '{}'.format(value[0])
            pickup_type = '{}'.format(value[1])
            drop_off_type = '{}'.format(value[2])
            distance_traveled = '{}'.format(value[3])

            # TODO Determine distance from previous stop

            # TODO Check that end stop in a trip has a time.

            # Required: trip_id, existing stop_id, stop_id, stop_sequence
            # Check that all the fields exist.
            if (trip_id is not None and stop_id is not None and stop_sequence is not None):
                # Check that the stop_id exists in stops.
                search = stop_id
                for stop in range(0, len(stops)):
                    if stops[stop][0] == search:

                        stop_time_line = '{},{},{},{},{},{},{},{},{}'.format(trip_id, arrival_time, departure_time, stop_id, stop_sequence, stop_headsign, pickup_type, drop_off_type,
                                                                             distance_traveled)
                        stop_time_data.append('{}\n'.format(stop_time_line))

                        if trip_id is not None and arrival_time is not None and departure_time is not None and stop_id is not None and stop_sequence is not None:
                            exception = 'Stop time value missingline i:{} stop:{} {},{},{},{},{} '.format(i, stops[stop],trip_id, arrival_time, departure_time, stop_id, stop_sequence)
                            write_exception_file(exception, worksheet_title, configs)

                        # Print the time points
                        # if arrival_time:
                        #     print("Time point --> i:{} j:{} with time:{} stop_id:{} seq#:{} startCheck:{}".format(i, j, departure_time, stop_id, stop_sequence, trip_start_check))

            else:
                # If stop_id is not in the stop.txt list, then skip it.
                exception = 'stop_id is not in stops list. trip line i:{} stop:{}'.format(i, stops[stop_sequence])
                write_exception_file(exception, worksheet_title, configs)
                continue

                        # color_trip_line = colored(stop_time_line, color='red', on_color='on_white'
                        # print('write_stop_times -->\n   {}\n'.format(color_trip_line))

    # Join the new list to existing list

    print('Writing stop_times data...')

    # Open and overwrite existing file
    f = open(gtfs_file, "a+")
    f.write(''.join(stop_time_data))
    f.close()

    print('Finished stop_times.txt, trips:{}.'.format(trip_count))

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
    gtfs_file = os.path.join(worksheet_name_output_dir, 'trips.txt')

    # File header
    x = GtfsHeader()
    x.write_header('trips', gtfs_file)


def write_shapes_header(worksheet_title, configs):

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)
    gtfs_file = os.path.join(worksheet_name_output_dir, 'shapes.txt')

    # File header
    x = GtfsHeader()
    x.write_header('shapes', gtfs_file)


def write_trips_file(trip_id, worksheet_title, worksheet, configs):
    '''
    Write trips values.

    route_id(r), service_id(r), trip_id(r), trip_headsign, trip_short_name, direction_id, block_id, shape_id,  wheelchair_acesible, bikes_allowed
    :param trip_id:
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

    if route_id is not None and service_id is not None and trip_id is not None:
    # If any required value is empty write exception and continue loop
        exception = 'Required value missing. trip line i:{} route_id:{} service_id:{} trip_id:{}'.format(i, route_id, service_id, trip_id)
        write_exception_file(exception, worksheet_title, configs)

    # Can't write trips header for each trip.
    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)
    gtfs_file = os.path.join(worksheet_name_output_dir, 'trips.txt')

    # Open and append to  existing file
    f = open(gtfs_file, "a+")
    f.write('{}\n'.format(trip_line))
    f.close()

    # c_trip_line = colored(trip_line,color='green', on_color='on_white')
    # print('write_trips_file trip_line:{}'.format(c_trip_line))
    print('Writing trip {}... to {}'.format(trip_id, gtfs_file))


def write_stops_file(worksheet_title, rows, worksheet, configs):
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
    stop        = ''
    ws_stops    = []

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)
    gtfs_file = os.path.join(worksheet_name_output_dir, 'stops.txt')

    # File header
    x = GtfsHeader()
    x.write_header('stops', gtfs_file)

    # Iterate across the valid rows. The worksheet data has 4 [rows] of static data.
    for i in range(3, len(rows)):

        # Required. Something must exist in the worksheet row to have been flagged.
        # Check to ensure a valid stop; must have stop_id, stop_name, stop_lat, stop_lon
        try:
            stop_id     = worksheet[i][3]
            stop_name   = worksheet[i][11]
            stop_lat    = worksheet[i][13]
            stop_lon    = worksheet[i][14]

        except IndexError:
            # Catch Out of Range error and write exception
            exception = 'IndexError. stop row i:{}'.format(i)
            write_exception_file(exception, worksheet_title, configs)
            c_exception = colored(exception, color='red')
            print(c_exception)
            continue


        cnt = 0
        value = []
        for k in range(10, 21):
            try:
                if worksheet[i][k] is None:
                    value.append('')
                else:
                    value.append(worksheet[i][k])
            except IndexError:
                value.append('')
            cnt += 1

        # Assign values to gtfs variables
        stop_code = value[0]
        stop_name = value[1]
        stop_desc = value[2]
        stop_lat = value[3]
        stop_lon = value[4]
        zone_id = value[5]
        stop_url = value[6]
        location_type = value[7]
        parent_station = value[8]
        stop_timezone = value[9]
        wheelchair_boarding = value[10]

        if stop_id is None or stop_name is None or stop_lat is None or stop_lon is None:
            # If any required value is empty write exception and continue loop
            exception = 'Required value missing. stop line i:{} stop_id:{} stop_name:{} stop_lat:{} stop_lon{}'.format(i, stop_id, stop_name, stop_lat, stop_lon)
            write_exception_file(exception, worksheet_title, configs)

        # Check to see if the stop was previously defined in worksheet.
        print('stop pre-check: id:{} name:{} lat:{} lon:{}'.format(stop_id, stop_name, stop_lat, stop_lon))
        # if stop_id not in stop:

        # Add stop to stops list for later merge
        stop = stop.split(',')
        ws_stops.append(stop)

        stop = ('{},{},{},{},{},{},{},{},{},{},{},{}'.format(stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon, zone_id, stop_url, location_type, parent_station, stop_timezone, wheelchair_boarding))

        c_stop_line = colored(stop, color='blue', on_color='on_white')
        print('write_stops --> stop_line:{}'.format(c_stop_line))

        # Open file for append
        f = open(gtfs_file, "a+")
        f.write('{}\n'.format(stop))
        f.close()

        # else: # Write exception
        #     exception = 'Stop_id in stop. i:{} stop_id:{} stop_name:{} stop_lat:{} stop_lon{}'.format(i, stop_id, stop_name, stop_lat, stop_lon)
        #     write_exception_file(exception, worksheet_title, configs)

    return ws_stops


def write_calendar_file(worksheet_title, worksheet, configs):
    '''
    Write a service calendar derived from the worksheet entries.
        Creates a service exception for the calendar service_id for each Holiday specified in the Config file.

    :param worksheet_title: Used to generate complete path to worksheet feed file.
    :param worksheet: Read the service_id and service DOW. Service dates are ignored as they are read from the Config.
    :param configs:
    :return:
    '''

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)
    gtfs_file = os.path.join(worksheet_name_output_dir, 'calendar.txt')

    # File header
    x = GtfsHeader()
    x.write_header('calendar', gtfs_file)

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
        write_exception_file(exception, worksheet_title, configs)

    # Placeholders for feed dates in spreadsheet are ignored.
    start_date  = configs.feed_start_date
    end_date    = configs.feed_end_date

    calendar_info = '{},{},{},{},{},{},{},{},{},{}\n'.format(service_id, monday, tuesday,
                                                             wednesday, thursday, friday, saturday, sunday,
                                                             start_date, end_date)

    if service_id is not None and monday is not (True or False) and tuesday is not (True or False) and wednesday is not (True or False) and thursday is not (True or False) and friday is not (True or False) and saturday is not (True or False) and sunday is not (True or False):
        # If any required value is empty write exception and continue loop
        exception = 'Required value missing. in calendar.'
        write_exception_file(exception, worksheet_title, configs)

    # Open and append to existing file
    f = open(gtfs_file, "a+")
    f.write('{}'.format(calendar_info))
    f.close()

    print('Writing calendar.txt to {}'.format(gtfs_file))


def write_calendar_dates_file(service_id, worksheet_title, configs):
    '''
    This function is called at the end of the write_calendar function, as the service_id required for
        the calendar_dates output is generated from the worksheet entries.
        Duplicates are stripped out of the feed later.
    :param worksheet_title:
    :param worksheet:
    :param configs:
    :return:
    '''

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)
    gtfs_file = os.path.join(worksheet_name_output_dir, 'calendar_dates.txt')

    # File header
    x = GtfsHeader()
    x.write_header('calendar_dates', gtfs_file)

    exception_type = '2'
    # TODO complete service exceptions
    dates = Calendar.ServiceExceptions(configs)
    print('Returned formatted dates:{}'.format(dates))

    # Setup a line entry for each holiday

    print('  service exception dates:{}'.format(dates))

    # Open and append date to existing file
    f = open(gtfs_file, "a+")
    for ex_day in dates:
        calendar_dates_info = '{},{},{}\n'.format(service_id, ex_day, exception_type)
        f.write('{}'.format(calendar_dates_info))
    f.close()

    print('Writing calendar_dates.txt to:{}...'.format(gtfs_file))


def write_routes_file(worksheet_title, worksheet, configs):

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)
    gtfs_file = os.path.join(worksheet_name_output_dir, 'routes.txt')

    # File header
    x = GtfsHeader()
    x.write_header('routes', gtfs_file)

    # REMEMBER Python counts begin at zero!
    # Worksheet data is in the third row; retrieved as the second list of row data.
    # Address the nested list-static data as list[1] (second list)

    # Collect all trips.txt values
    value = []
    for i in range(10, 18):
        if worksheet[1][i] is not None:
            value.append(worksheet[1][i])
        else:
            value.append('')

    route_id            = value[0]
    agency_id           = configs.agency_id
    route_short_name    = value[1]
    route_long_name     = value[2]
    route_desc          = value[3]
    route_type          = value[4]
    route_url           = value[5]
    route_color         = value[6]
    route_text_color    = value[7]

    route_info = '{},{},{},{},{},{},{},{},{}\n'.format(route_id, agency_id, route_short_name,
                                                    route_long_name, route_desc, route_type, route_url, route_color,
                                                    route_text_color)
    print('Writing routes.txt to {}'.format(gtfs_file))

    # Open and append to existing file
    f = open(gtfs_file, "a+")
    f.write('{}'.format(route_info))
    f.close()


def write_feed_info_file(worksheet_title, configs):

    worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)
    gtfs_file = os.path.join(worksheet_name_output_dir, 'feed_info.txt')

    # File header
    x = GtfsHeader()
    x.write_header('feed_info', gtfs_file)

    feed_info = '{},{},{},{},{},{}\n'.format(configs.feed_publisher_name, configs.feed_publisher_url, configs.feed_lang,
                                             configs.feed_start_date, configs.feed_end_date, configs.feed_version)

    print('Writting feed_info.txt to {}'.format(gtfs_file))


    # Open and overwrite existing file
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
    gtfs_file = os.path.join(worksheet_name_output_dir, 'agency.txt')

    # Overwrite with file header
    x = GtfsHeader()
    x.write_header('agency', gtfs_file)

    # Agency.txt information
    agency_info = '{},{},{},{},{},{}'.format(str(configs.agency_id), str(configs.agency_name), str(configs.agency_url),
                                             str(configs.agency_timezone), str(configs.agency_lang), str(configs.agency_phone))

    print('Writing agency.txt to {}'.format(gtfs_file))

    # Write info line to file
    f = open(gtfs_file, "a+")
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
    gtfs_file = os.path.join(worksheet_name_output_dir, 'fare_rules.txt')

    # File header
    x = GtfsHeader()
    x.write_header('fare_rules', gtfs_file)

    # Fare_rules are in the configuration file. Make config string into list.
    fare_ids        = configs.fare_ids.split(',')
    route_ids       = ''
    origin_ids      = ''
    destination_ids = ''
    contains_ids    = ''
    # Construct line info
    for i in range(len(fare_ids)):
        line = '{},{},{},{},{}\n'.format(fare_ids[i], route_ids, origin_ids, destination_ids, contains_ids)
        # Write info line to file
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
    gtfs_file = os.path.join(worksheet_name_output_dir, 'fare_attributes.txt')

    # Overwrite with file header
    x = GtfsHeader()
    x.write_header('fare_attributes', gtfs_file)

    # Fare_rules are in the configuration file. Make config string into list.
    fare_ids = configs.fare_ids.split(',')
    prices  = configs.prices.split(',')
    transfers = configs.transfers.split(',')
    durations = configs.durations.split(',')
    # Construct line info
    for i in range(len(fare_ids)):
        line = '{},{},{},{},{},{}\n'.format(fare_ids[i], prices[i], configs.currency, configs.payment_method, transfers[i], durations[i])
        # Write info line to file
        f = open(gtfs_file, "a+")
        f.write('{}'.format(line))
    f.close()


def create_exceptions_file(current_worksheet_title, configs):
    # Clear exceptions file with over write
    worksheet_name_output_dir = get_worksheet_name_output_dir(current_worksheet_title, configs)
    exception_file = os.path.join(configs.report_path, 'exceptions.dat')
    # Overwrite existing file
    f = open(exception_file, "w+")
    f.write('Worksheet:{}\n'.format(current_worksheet_title))
    f.close()


def write_exception_file(exception, worksheet_title, configs):

    # TODO Delete this
    # worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)

    exception_file = os.path.join(configs.report_path, 'exceptions.dat')

    # Open and append existing file (clear the file before opening the worksheet)
    f = open(exception_file, "a+")
    now = datetime.now()
    f.write('{}     worksheet:{}\n   {}   '.format(now, worksheet_title, exception))
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


def write_shape_from_kml(shapeID, title, configs):
    """
    Function constructs a .kml and .txt filename from the worksheet entry.

    If the kml_txt exists, then the text file contains two or more kml entries to be concatenated together into
        a GTFS shapes.txt file.
    If the kml_txt does not exist, then the kml_file is processed as a singlton into a GTFS shapes.txt file.

    :param shapeID: The shapeID from worksheet
    :param configs:
    :return:
    """

    tripKML = '{}.kml'.format(shapeID)
    tripKML_loc = os.path.join(os.path.expanduser(configs.kml_files_root), tripKML)
    tripKML_txt_file = '{}.txt'.format(shapeID)
    tripKML_txt_loc = os.path.join(os.path.expanduser(configs.kml_files_root), tripKML_txt_file)

    print('  Looking for KML file or list: {} from worksheet:{} in path\n   KML {}\n   TXT {}'.format(shapeID, title, tripKML_loc, tripKML_txt_loc))

    shape_out = 'Not assigned'

    worksheet_name = title

    shapetxt_out = os.path.join(os.path.expanduser(configs.gtfs_path_root), worksheet_name, 'shapes.txt')
    print('  shapes.txt output to:{}'.format(shapetxt_out))

    try:
        # Single KML file processing.
        if os.path.isfile(tripKML_loc):

            c_shapeKML = colored('  Found KML:{} in directory: {}'.format(tripKML, configs.kml_files_root), color='blue')
            print(c_shapeKML)

            shape_out = os.path.join(os.path.expanduser(configs.gtfs_path_root), tripKML)

            last_sequence_number = 0
            accumulated_distance = 0.0
            allNameElements, allCoordsElements = get_kml_elements(tripKML_loc)
            write_coords_to_file(shapetxt_out, allNameElements, allCoordsElements, shapeID, last_sequence_number,
                                 accumulated_distance)

        # Multiple KML file processing. Read KML filenames from a text file with the name of the shapeID.
        elif os.path.isfile(tripKML_txt_loc):

            c_shapeTXT = colored('  Found TXT: {} in directory: {}'.format(tripKML_txt_loc, configs.kml_files_root), color='green')
            print(c_shapeTXT)

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
                    last_sequence_number, accumulated_distance = write_coords_to_file(shapetxt_out, allNameElements, allCoordsElements, shapeID, last_sequence_number, accumulated_distance)

    except IOError:
        c_neg = colored('  KML nor TXT: {} found in directory: {}'.format(tripKML, configs.kml_files_root), color='red')
        print(c_neg)

        # TODO Write KML error to log

    # print('Writing shape.txt from KML.\n  --> kml root:{}\n  -->shapeID:{}\n  -->path:{}'.
    #       format(configs.kml_files_root, shapeID, tripKML))

    # print("File '{}' processed.\n    with {:,} nodes and a total distance of {:.2f} miles.".
    #       format(configs.file_list[i], last_sequence_number, accumulated_distance))
    c_note = colored('{} Completed KML to shape for {}.txt. {}'.format('<' * 5, shapeID, '>' * 5),color='green')
    print(c_note)


def get_vincenty_distance(point1, point2):
    # Calculate the distance between to lat/long pairs
    d = vincenty(point1, point2).miles
    return d


def write_shape_line(shape_txt_out, shapeID, lat2, lng2, last_sequence_number, accumulated_distance, distance):
    # Write each output line in shapes.txt

    f = open(shape_txt_out, 'a')
    line_out = "{}, {:.6f}, {:.6f}, {}, {:.2f}, {:.3f}\n".format \
        (shapeID, lat2, lng2, last_sequence_number, accumulated_distance, distance)

    # print('  write_shape_line:{}'.format(line_out))

    f.write(line_out)


def write_coords_to_file(shape_txt_out, allNameElements, allCoordsElements, shapeID, last_sequence_number,
                          accumulated_distance):
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
                    distance = get_vincenty_distance(point1, point2)
                # Accumulate sequence number
                last_sequence_number += 1

                # Accumulate shape distances
                accumulated_distance = distance + accumulated_distance

                # Write the line to the shapes.txt file
                write_shape_line(shape_txt_out, shapeID, lat2, lng2, last_sequence_number, accumulated_distance,
                                 distance)
                # Assign coordinates to previous
                lat1 = lat2
                lng1 = lng2

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
    subprocess.run(['feedvalidator.py','-n','-o','{}'.format('validator.html'), '{}'.format(gtfs_zip)])


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


def get_google_worksheet_data(row_list, worksheet):
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


def write_run_info_to_file(start_time, stop_time, title, note, configs):
    # Open and append to  existing file
    f = open(configs.stats_file, "a+")
    tdelta = stop_time - start_time
    info_header = '  {} {}'.format(note, title)
    run_info = '      Elapsed time:{} '.format(tdelta)
    f.write('{}\n{}\n'.format(info_header, run_info))
    f.close()


def read_worksheet_data_from_csv(current_worksheet_title, configs):
    ## TODO read_worksheet_data_from_csv not tested. Pickle the output
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
    tdelta_colored = colored(tdelta, text_color, 'on_grey')
    c_note = colored(note, color=text_color)
    print('   {} ET. {} present date/time:{}'.format(tdelta_colored, c_note, stop_time))
    write_run_info_to_file(start_time, stop_time, title, note, configs)


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

    create_gtfs_zip(os.path.expanduser(configs.gtfs_path_root), agency_ID)
    # Validate the master
    path = os.path.expanduser(configs.gtfs_path_root)
    filename = configs.agency_id
    run_validator(path, filename, configs)


def combine_files(worksheets, configs):
    '''
    Combine individual GTFS files gnerated from worksheets.
    :param worksheets: List of processed worksheets
    :return:
    '''

    import fileinput

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


def main (argv=None):
    # Let the user know the python version and platform that the app is running on
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
            # Call the test function

            service_id = '?'
            worksheet_title = 'test_worksheet'
            write_calendar_dates_file(service_id, worksheet_title, configs)

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        elif configs.generate is True:

            # <<<<<<<<<< Generate Generate Generate Generate Generate >>>>>>>>>>

            print("generating...\n")
            start_time = datetime.now()
            note = '{}'.format('{}\nStart processing {} workbook {}.'.format(start_time, configs.agency_id, configs.google_workbook_name))
            c_note = colored(note,color='green',on_color='on_grey')
            print(c_note)
            print_et(text_color='green', start_time=start_time, title='Workbook start.', note=note, configs=configs)

            # Google workbook; get G_workbook name from configs and worksheets object from the G_workbook.
            route_workbook = open_google_workbook(defaults, configs)
            worksheets = route_workbook.worksheets()
            # print('worksheets:{}'.format(worksheets))

            # Select the sheets to process. Create empty list to hold processed sheet titles.
            sheets  = []

            for worksheet in worksheets:
                sheets.append(worksheet.title)
            print('sheets:{}'.format(sheets))
            p_sheets   = []

            # Exclude worksheets named Master and Template
            ignore_list = configs.ignore_sheets.split(',')
            print('ignore list:{}'.format(ignore_list))

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

                        # Put an exceptions file in the directory
                        create_exceptions_file(current_worksheet_title, configs)
                        print('Creating exceptions file...')

                        # Required rows: r2=headings(optional) r3=data r6=trip headings from configuration
                        # Cast list as integer values

                        head_data_rows = [int(s) for s in configs.head_data_rows.split(",")]

                        # Required columns: 2=stop seq 3=stopID 10-21=stop info 22-25=trip info from configuration file.
                        stops_column_list = [int(s) for s in configs.stop_data_columns.split(",")]

                        # Print the current worksheet title in color
                        current_worksheet_colored = colored(worksheet.title, 'green', 'on_grey')
                        print('{}'.format(current_worksheet_colored))

                        # TODO: Process any type of worksheet;  .xls, csv, or .ods
                        # http://davidmburke.com/2013/02/13/pure-python-convert-any-spreadsheet-format-to-list/

                        # TODO Add get_stop_times_rows as a function.
                        # Get stop_times rows.
                        note = '{}'.format('')
                        print_et(text_color='green', start_time=start_time, title='Start worksheet data retrieval.', note=note,
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
                        write_calendar_file(worksheet_title=current_worksheet_title, worksheet=ws_data, configs=configs)

                        # Calendar_dates.txt processing
                        # TODO rework service exception determination
                        service_id = ws_data[1][28]
                        write_calendar_dates_file(service_id, worksheet_title=current_worksheet_title, configs=configs)

                        # Stops.txt processing
                        #   Collect stops in memory for later merge.
                        ws_stops = write_stops_file(worksheet_title=current_worksheet_title, rows=row_list,
                                                    worksheet=ws_data, configs=configs)

                        note = '{}'.format('')
                        print_et(text_color='green', start_time=start_time, title='Stops processing.', note=note,
                                 configs=configs)

                        # Trips.txt header. Trips are written from stop_times.txt processing
                        write_trips_header(worksheet_title=current_worksheet_title, configs=configs)
                        note = '{}'.format('')
                        print_et(text_color='green', start_time=start_time, title='Stop_times processing.', note=note,
                                 configs=configs)

                        # Stop times and trips processing
                        write_stop_times_file(worksheet_title=current_worksheet_title, rows=row_list, columns=stops_column_list, stops=ws_stops, worksheet=ws_data, configs=configs)
                        note = '{}'.format('')
                        print_et(text_color='green', start_time=start_time, title='Start shapes.txt from kml.',
                                 note=note, configs=configs)

                        # Write_shapes.txt processing
                        write_shapes_header(worksheet_title=current_worksheet_title, configs=configs)
                        shapeID     = ws_data[1][25]
                        print('shapeID:{}'.format(shapeID))
                        write_shape_from_kml(shapeID=shapeID, title=current_worksheet_title, configs=configs)

                        print('Worksheet {} complete.'.format(current_worksheet_title))
                        note = '{}'.format('')
                        print_et(text_color='green', start_time=start_time, title='Worksheet {} complete.'.format(current_worksheet_title),
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

                        # Add worksheet title to list of processed worksheets for merge function
                        p_sheets.append(current_worksheet_title)

            # Merge feeds in the processed sheets list
            print('\nCombining {} gtfs feeds from {}'.format(len(p_sheets),p_sheets))
            note = '{}'.format('')
            print_et(text_color='green', start_time=start_time, title='Combining worksheets {}.'.format(p_sheets), note=note, configs=configs)
            combine_gtfs_feeds(worksheets=p_sheets, configs=configs)

            # Startup the schedule_viewer with the master GTFS.zip
            # run_schedule_viewer(configs)

            print_et(text_color='red', start_time=start_time, title='Finished processing.', note='END',
                     configs=configs)
            print('')



        elif (configs.demo is True):
            print("Demo")

        else:

            print(colored("Defaults are of type None.", 'cyan'))

        return 0


if __name__ == '__main__':
    sys.exit(main())
