__author__ = 'Dr. Pete Dailey'

# Import Pandas
import pandas as pd
from pandas.tseries.holiday import Holiday, AbstractHolidayCalendar
from pandas.tseries.holiday import MO, TU, TH, FR, nearest_workday
from pandas.tseries.offsets import *
from pandas.tseries.holiday import USMemorialDay, USLaborDay, USColumbusDay, USThanksgivingDay, USMartinLutherKingJr, USPresidentsDay, GoodFriday, EasterMonday
from termcolor import colored


# class ServiceExceptions(object):
#  From "Writing Idiomatic Python" - use of dictionary
#       user_email = {user.name: user.email
#           for user in users_list if user.email}
#     def __init__(self, configs):

def ServiceExceptions(configs):
    """
    This functions runs the retrieval of the dates for US and WV holidays specified in the configuration file between\
      the dates specified after the time span specified.
    :param configs: the configuration object that contains dates and holiday names.
    :return: a list containing strings of dates in %Y%m%d format.
    """

    start_date      = configs.feed_start_date
    end_date        = configs.feed_end_date
    holiday_list    = configs.holidays
    delta_max       = configs.delta_max

    if not start_date:
        print(colored('No start date, assuming today.', 'red'))
        start_date = pd.datetime.today().strftime('%Y%m%d')
    if not end_date:
        print(colored('No end date, adding delta of {} to start.', 'red').format(delta_max))
        end_date = pd.datetime(start_date) + pd.DateOffset(days=delta_max)
    if not holiday_list:
        print(colored('No holidays specified.', 'red'))

    cal_dates = get_dates(start_date, end_date, configs)

    return cal_dates


def unify_holiday_names(configs):
    """
    The function forces all the holday names to:
        1. lowercase
        2. strip apostraphes
        3. strip whitespaces
        4. **opt: 'simplify' names? identify alternate names (July 4th == Independence Day, MLK = Martin Luther)
    :param configs: From config file, contains the list of holidays
    :return: List containing unified holiday names
    """
    # TODO write unify code


def get_dates(start, end, configs):
    """
    This function retrieves every holiday date refined in the UsaWvCalendar class the between the dates specified.
    :param begin_date: Holiday calendar begining date in datetime-like string
    :param end: Holiday calenday ending date in a datetime-like string
    :param dt_max: Maximum days between begining and end - GTFS feed not allowed to be > 365 days.
    :param configs: contains a list of holidays
    :return: cal_dates, a list of strings containing the holidays in GTFS date format.
    """

    holiday_list = configs.holidays
    delta_max   = configs.delta_max
    # start = pd.Timestamp(start)
    # end   = pd.Timestamp(end)
    print(' From GtfsCalendar.getDates start:{} end:{} max delta days:{}'.format(start, end, delta_max))

    my_calendar = determine_calendar_dates(start, end, configs)
    # print('  from GtfsCalendar.getDates my_calendar\n{}'.format(vars(my_calendar)))
    my_dates = select_agency_calendar_dates(my_calendar, configs)

    cal_dates = []

    for index, date in enumerate(my_dates):
        # print('  >> date {}: {}'.format(index, date.strftime('%Y%m%d')))
        # Check for duplicate dates
        if date not in cal_dates:
            cal_dates.append(date.strftime('%Y%m%d'))
    # print(cal_dates)

    return cal_dates


def determine_calendar_dates(start_date, end_date, configs):
    """
    This function determines all the holidays defined in the USA-WV Calendar class between the start and end dates.
    :param start_date:
    :param end_date:
    :param dt_max:
    :return:
    """

    cal = UsaWvCalendar()
    start, end = check_calendar_length(start_date, end_date, configs)
    calendar = cal.holidays(start, end, return_name=True)

    return calendar


def check_calendar_length(start, end, configs):
    """
    This function checks the number of days between the start and stop dates, if greater than the max_length, the
        end date is calculated from the start date.
    :param start: starting date of the calendar in a datetime-like
    :param end: ending date of the calendar
    :param max_length: maximum number of days from start to end
    :return: start and stop dates for calendar determination.
    """

    # Text to Pandas Timestamps
    start = pd.Timestamp(start)
    end   = pd.Timestamp(end)
    delta = end - start
    # print (' From check_calendar_length - delta days between start and stop:{}'.format(delta))
    # If a delta max is specified in the configuration file use it, else default to 1 year.
    if configs.delta_max:
        offset = int(configs.delta_max)
    else:
        offset = 365
    # If the the start and end days are greater than the configuration file maximum, add the configuration maximum days
    #   to the start date. *** GTFS feedfiles can not exceed 1 year.
    if delta > pd.Timedelta(days=offset):
        new_end = start + DateOffset(days=int(configs.delta_max))
        print(colored(('Start to end length exeeded, calculated {} days, max is {} days.'.format\
                           (delta, configs.delta_max)),color='red'))
        # TODO write exception
        start   = start.strftime('%Y%m%d')
        new_end = new_end.strftime('%Y%m%d')
    # Start and Stop are good, return unchanged.
    else:
        start   = start.strftime('%Y%m%d')
        new_end = end.strftime('%Y%m%d')

    print(colored(' >> New start date is {}, end date is {}.'.format(start, new_end), color='green'))

    # Return start and end as GTFS formated date strings
    return start, new_end


def select_agency_calendar_dates(calendar, configs):
    """
    This function selects the calendar dates that match the configs holiday name list.
    :param calendar: calendar of all holidays in UsaWvCalendar class.
    :param configs: contains a list of holidays from the configs file.
    :return:
    """
    holiday_list = configs.holidays
    dates = []
    for index, day in enumerate(calendar):
        print('From all holidays index:{} day:{}'.format(index, day))
        if calendar.values[index] in holiday_list:
            # print(colored(' >>> Found my date:{}  my holiday:{}'.format(calendar.index[index].strftime('%Y%m%d'), calendar.values[index]), color='green'))
            dates.append(calendar.index[index])
    return dates


def election_observance(dt):
    if dt.year % 2 == 1:
        dt = pd.to_datetime('1/1/2000')
        return dt
    else:
        return dt + pd.DateOffset(weekday=TU(1))


class UsaWvCalendar(AbstractHolidayCalendar):
    """
    All the US and WV holidays my transit agencies may observe.

    """
    rules = [
        Holiday('New Years Day', month=1,  day=1,  observance=nearest_workday),
        USMartinLutherKingJr,
        USPresidentsDay,
        USMemorialDay,
        Holiday('July 4th', month=7,  day=4,  observance=nearest_workday),
        Holiday('Independence Day', month=7,  day=4,  observance=nearest_workday),
        USLaborDay,
        USColumbusDay,
        Holiday('Veterans Day', month=11, day=11, observance=nearest_workday),
        USThanksgivingDay,
        Holiday('Day After Thanksgiving Day', month=11, day=1, offset=DateOffset(weekday=FR(4))),
        Holiday('Christmas', month=12, day=25, observance=nearest_workday),
        GoodFriday,
        EasterMonday,
        Holiday('US Election Day', month=11, day=1, observance=election_observance),
        Holiday('WV Primary Election Day', month=5, day=1, observance=election_observance),
        Holiday('WV Day', month=6, day=20),
    ]