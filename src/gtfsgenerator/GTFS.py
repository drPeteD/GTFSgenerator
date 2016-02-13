__author__ = 'dr.pete.dailey'

import os

class GtfsHeader:
    '''    The Header class opens/overwrites the GTFS file and inserts a header line.

     Attributes:
        name: gtfs file name (without the 'txt' extension)
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
        shapes          = 'shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence,shape_dist_traveled'
        # Distance from previous point removed from shape.txt
        # shapes          = 'shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence,shape_dist_traveled,dist_from_previous'
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

    def write_header(self, filename, worksheet_name_dir):
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

        # Open and overwrite existing file:
        print('{}--> <<< Does directory {} exist? {}'.format(filename, worksheet_name_dir, os.path.exists(worksheet_name_dir)))
        if os.path.exists(worksheet_name_dir):
            # print(colored('  >>> Directory exists:{} <<<'.format(worksheet_name_dir)),color='green')
            print('  >>> Directory exists:{} <<<'.format(worksheet_name_dir))

        else:
            os.makedirs(worksheet_name_dir)
            # print(colored('  >>> Created directory:{} <<<'.format(worksheet_name_dir)),color='red')
            print('  >>> Created directory:{} <<<'.format(worksheet_name_dir))

        filename = filename + '.txt'
        f = open(os.path.join( worksheet_name_dir, filename ), 'w')
        f.write('{}\n'.format(header))
        f.close()


# class GtfsWrite():
#     '''
#     Write the specified file
#     '''
#
#     def __init__(self, configs):
#         '''
#         Write the agency.txt file data in the location specified by the path.
#         :param header_flag: True=overwrite file with header. False pass the information line
#         :param row_data: A line of data
#         :param path: Location of agency.txt
#         :param args: Not sure what is needed from args, path?
#         :return:
#         '''
#         self.agency = configs.agency
#
#
#     def get_output_dir_name(configs):
#
#     # output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'output'))
#
#         output_dir = os.path.expanduser(configs.gtfs_path_root)
#
#     # print('get_output_dir_name ***+++ output_dir-test +++:{}'.format(output_dir))
#     # print('get_output_dir_name *** configs.gtfs_path_root ***:{}'.format(configs.gtfs_path_root))
#     # output_dir = os.path.abspath(os.path.dirname(configs.gtfs_path_root))
#     # print('get_output_dir_name ***> output_dir <---:{}'.format(output_dir))
#
#         return output_dir
#
#
#     def create_output_dir(configs):
#
#         output_dir = get_output_dir_name(configs)
#         if not os.path.exists(output_dir):
#             os.makedirs(output_dir)
#
#
#     def get_worksheet_name_output_dir(worksheet_title, configs):
#         '''
#         Get the fully qualified output directory name from Config file and worksheet title.
#         If title is 'master', then use the top level directory from Config file.
#         :param worksheet_title:
#         :param configs:
#         :return:
#         '''
#
#         output_dir = get_output_dir_name(configs)
#         worksheet_name_output_dir = os.path.join(output_dir, worksheet_title)
#
#         return worksheet_name_output_dir
#
#     def agency(self,header_flag,row_data,path,args):
#
#         return
#
#
#     def write_stops_file(worksheet_title, rows, worksheet, configs):
#         """
#         GTFS stops.txt file from worksheet output in csv format with key values:
#         stop_id,stop_code,stop_name,stop_desc,stop_lat,stop_lon,zone_id,stop_url,location_type,parent_station,
#         stop_timezone,wheelchair_boarding
#
#         :param worksheet_title: Google Sheets worksheet name
#         :param configs: configuration file values
#         :param worksheet:
#         :return None
#         """
#         # Keep a stops list of all stops in memory for stop_times stop_id check.
#         stop_list = []
#
#         worksheet_name_output_dir = get_worksheet_name_output_dir(worksheet_title, configs)
#
#         # File header
#         x = GtfsHeader()
#         x.write_header('stops', worksheet_name_output_dir)
#
#         # Iterate across the valid rows. The worksheet data has 4 [rows] of static data.
#         stop_list = []
#         for i in range(3, len(rows)):
#
#             # Required. Something must exist in the worksheet row to have been flagged.
#             # Check to ensure a valid stop; must have stop_id, stop_name, stop_lat, stop_lon
#             try:
#                 # Required
#                 stop_id     = worksheet[i][3]
#                 stop_name   = worksheet[i][11]
#                 stop_lat    = worksheet[i][13]
#                 stop_lon    = worksheet[i][14]
#                 # Optional
#                 stop_code   = worksheet[i][10]
#                 stop_desc   = worksheet[i][12]
#                 zone_id     = worksheet[i][15]
#                 stop_url    = worksheet[i][16]
#                 loc_type    = worksheet[i][17]
#                 parent      = worksheet[i][18]
#                 timezone    = worksheet[i][19]
#                 wheel_board = worksheet[i][20]
#
#             except IndexError:
#                 # Catch Out of Range error and write exception
#                 exception = 'IndexError. stop row i:{}'.format(i)
#                 write_exception_file(exception, worksheet_title, configs)
#                 c_exception = colored(exception, color='red')
#                 print(c_exception)
#                 continue
#
#             if stop_id and stop_name and stop_lat and stop_lon:
#                 # Format stop line output
#                 stop = ('{},{},{},{},{},{},{},{},{},{},{},{}'.format(stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon, zone_id, stop_url, loc_type, parent, timezone, wheel_board))
#
#                 # Check to see if stop exists, write to exception if true.
#                 if stop in stop_list:
#                     exception = 'Duplicate stop row {} :{}'.format(i, stop)
#                     write_exception_file(exception, worksheet_title, configs)
#                     print(exception)
#                 # Write to stop_list if it does not exist. Print the stop to console.
#                 else:
#                     stop_list.append(stop)
#                     c_stop_line = colored(stop, color='blue', on_color='on_white')
#                     print('write_stops --> stop_line:{}'.format(c_stop_line))
#             else:
#                 # TODO Move this check before append to list.
#                 # If any required value is empty write exception and continue loop
#                 exception = 'Required value missing. stop line i:{} stop_id:{} stop_name:{} stop_lat:{} stop_lon{}'.format(i, stop_id, stop_name, stop_lat, stop_lon)
#                 write_exception_file(exception, worksheet_title, configs)
#
#         # Write stop_list to stops.txt
#         gtfs_file = os.path.join(worksheet_name_output_dir, 'stops.txt')
#         f = open(gtfs_file, "a+")
#         for stop in stop_list:
#             f.write('{}\n'.format(stop))
#         f.close()
#
#         return stop_list




