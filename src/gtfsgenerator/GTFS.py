__author__ = 'dr.pete.dailey'

import os


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

        # Open and overwrite existing file:
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path)) # make directory from full path
            print('  >>> Created directory:{} <<<'.format(os.path.dirname(path)))
        try:
            f = open(path, 'w')
            f.write('{}\n'.format(header))
            f.close()
        except: # FileNotFoundError:
            # write exception
            print('Write exception at write_header.')
