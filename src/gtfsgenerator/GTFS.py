#!/usr/bin/env python

__author__ = 'dr.pete.dailey'

import fileinput
import os


class GtfsHeader():
    '''
    The Header class opens/overwrites the GTFS file and inserts a header line.

     Attributes:
        name: gtfs file name (without the 'txt' extension)
        path: path to output location
        config: arguments from a configuration file
    '''

    def __init__ (self):
        # Anything to init?
        # self.gtfs_filelist = ['agency','calendar','calendar_dates','fare_attributes','fare_rules','feed_info','routes',\
        #                  'shapes','stop_times','stops','trips']
        # return self.gtfs_filelist
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
        # shapes          = 'shape_id,shape_pt_lat,shape_pt_lon,shape_pt_sequence,shape_dist_traveled'
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

        # Open and overwrite existing file:
        # print('{}--> <<< Does directory {} exist? {}'.format(filename, path, os.path.exists(path)))
        if os.path.exists(path):
            # print('  >>> Directory exists:{} <<<'.format(path))
            pass
        else:
            os.makedirs(path)
            # print('  >>> Created directory:{} <<<'.format(path))

        filename = filename + '.txt'
        f = open(os.path.join(path, filename), 'w')
        f.write('{}\n'.format(header))
        f.close()

    def return_header(self, filename):
        # Get file header
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
        return header

    def remove_head_line(self, gtfs_file, path):
        """
        Remove and replace GTFS header in a GTFS file.
        :param gtfs_file: GTFS file name, ie., stops, stop_times, trips.
        :param path: Input file path, combined feed files.
        :return:
        """
        out_list = []
        header = GtfsHeader.return_header(self, gtfs_file).strip()
        in_file = os.path.join(os.path.expanduser(path), '{}.tmp'.format(gtfs_file))

        lines = open(in_file).readlines()
        cnt = 0
        for line in lines:
            if header in line:
                cnt += 1
                print('>>> Found header {} in {}.'.format(cnt, gtfs_file))
                lines.remove(line)
        # out_list.append(header.strip())

        for line in lines:
            out_list.append(line.strip())
        out_file = in_file

        f = open(out_file, 'w')
        for line in out_list:
            f.write('{}\n'.format(line.strip()))
        f.close()


class GtfsWrite():
    '''
    The Write class manipulates GTFS files.

     Attributes:
        name: gtfs file name (without the 'txt' extension)
        path: path to output location
        config: arguments from a configuration file
    '''

    def __init__(self):
        self.gtfs_filelist = ['agency','calendar','calendar_dates','fare_attributes','fare_rules','feed_info','routes',\
                 'shapes','stop_times','stops','trips']
        self.agency_format = '{},{},{},{},{},{}'
        self.calendar_format = '{},{},{},{},{},{},{},{},{},{}'
        self.calendar_dates_format = '{},{},{}'
        self.fare_attributes_format = '{},{},{},{},{},{}'
        self.fare_rules_format = '{},{},{},{},{}'
        self.feed_info_format = '{},{},{},{},{},{}'
        self.route_format = '{},{},{},{},{},{},{},{},{}'
        self.shapes_format = line_out = '{}, {:.6f}, {:.6f}, {}, {:.2f}'
        self.stop_times_format = '{},{},{},{},{},{},{},{},{}'
        self.stops_format = '{},{},{},{},{},{},{},{},{},{},{},{}'
        self.trips_format = '{},{},{},{},{},{},{},{},{},{}'


    def remove_dup_lines(self, in_file):
        """
        Remove duplication lines from a GTFS file. Optionaly finding and replacing header at top of file.
        :param replace_head: Boolean to replace GTFS file header.
        :param gtfs_file: GTFS file name.
        :param in_file: Path to file.
        :return:
        """
        lines = open(in_file, 'r').readlines()
        lines_in = len(lines)
        lines_set = sorted(set(lines))
        lines = list(lines_set)
        lines_out = len(lines)
        lines_removed = int(lines_in ) - int( lines_out)
        print('Lines removed:{}, lines in_file:{} lines returned:{}'.format(lines_removed, lines_in, lines_out))
        out_file = in_file
        out = open( out_file, 'w' )
        for line in lines_set:
            out.write(line)
        out.close()


    def combine_files(self, wrkbk_dict, configs):
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
            Combine individual GTFS files from wrkbk_dict.
                module 'fileinput'
        :param wrkbk_dict: Dictionary of workbook/worksheet pairs.
        :return:
        '''

        gtfs_filelist = ['agency','calendar','calendar_dates','fare_attributes','fare_rules','feed_info','routes','shapes',
                     'stop_times','stops','trips']




        for gtfs_file in gtfs_filelist:

            gtfs_tmp = '{}.tmp'.format(gtfs_file)
            out_path = os.path.expanduser(configs.gtfs_path_root)
            out_tmp = os.path.join(out_path, gtfs_tmp)
            gtfs_master = '{}.txt'.format(gtfs_file)

            # Combine gtfs_files for all wrkbk_dict
            # ref:http://stackoverflow.com/questions/13613336/python-concatenate-text-files
            # ref os glob tool: http://www.diveintopython3.net/comprehensions.html

            for key, value in wrkbk_dict.items(): #iterate across workbooks
                print('Combine workbook {} with {} worksheets:'.format(key, len(wrkbk_dict[key])))
                # iterate across worksheets in workbook for each gtfs file
                for i in range(len(value)):
                    print('Retreive Workbook:{} Worksheet:{} GTFS file:{}.txt'.format(key,value[i], gtfs_file))

                    # Construct the input file path to trip group locations - e.g., gtfs/workbook/worksheet/gtfs.txt.
                    input_dir = os.path.join(os.path.expanduser(configs.gtfs_path_root), key, value[i] )
                    infile = os.path.join(input_dir, '{}.txt'.format(gtfs_file))

                    # Combine lines in fin and fout
                    with open(out_tmp, 'a') as fout, fileinput.input(infile) as fin:
                        for line in fin:
                            fout.write(line)
                        fout.close()
                fout = open(out_tmp, 'a')
                # Remove duplicate lines, remove headers.
                x = GtfsHeader()
                x.remove_head_line(gtfs_file, out_path)
                print('Removing duplicate lines from {}.'.format(gtfs_tmp))
                GtfsWrite.remove_dup_lines(self, os.path.join(out_path, gtfs_tmp))
                x.write_header(gtfs_file, out_path)
                fout.close()
                with open(os.path.join(out_path, gtfs_master), 'a') as fout, fileinput.input(os.path.join(out_path, gtfs_tmp), 'r') as fin:
                    for line in fin:
                        fout.write(line)
                    fout.close()
                os.remove(os.path.join(out_path, '{}.tmp'.format(gtfs_file)))


    def write_agency_file(workbook, worksheet_title, configs):
        '''
        Write agency.txt from values in configuration file.

        :param worksheet_title: present worksheet name. If none then the 'master' GTFS feed.
        :param configs: arguments from the configuration file.
        :return:
        '''

        wrkbk_wrksht_output_dir = os.path.join(os.path.expanduser(configs.gtfs_path_root), workbook, worksheet_title)

        x = GtfsHeader()
        x.write_header('agency', wrkbk_wrksht_output_dir)

        print('Writing agency.txt to {}'.format(wrkbk_wrksht_output_dir))
        agency_info = '{},{},{},{},{},{}'.format(str(configs.agency_id), str(configs.agency_name), str(configs.agency_url),
                                                 str(configs.agency_timezone), str(configs.agency_lang), str(configs.agency_phone))

        f = open(os.path.join(wrkbk_wrksht_output_dir,'agency.txt'), "a+")
        f.write('{}\n'.format(agency_info))
        f.close()
