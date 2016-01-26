__author__ = 'Dr. Pete Dailey'

# Import Pandas
import pandas as pd
from pandas.tseries.holiday import Holiday, AbstractHolidayCalendar
from pandas.tseries.holiday import MO, TU, TH, FR, nearest_workday
from pandas.tseries.offsets import *
from pandas.tseries.holiday import USMemorialDay, USLaborDay, USColumbusDay, USThanksgivingDay, USMartinLutherKingJr, USPresidentsDay, GoodFriday, EasterMonday
from termcolor import colored


# class ServiceExceptions(object):
#
#     def __init__(self, configs):

def ServiceExceptions(configs):
    """

    :param configs:
    :return:
    """

    start_date = configs.feed_start_date
    end_date   = configs.feed_end_date
    delta_max  = configs.delta_max
    holidays   = configs.holidays
    if not start_date:
        print(colored('No start date.', 'red'))
    if not end_date:
        print(colored('No end date.', 'red'))
    if not delta_max:
        print(colored('No maximun feed length (days) specified.', 'red'))

    getDates(start_date, end_date, delta_max, holidays)


def getDates(self, start_date, end_date, delta_max, holidays):
    """

    :param begin_date:
    :param end_date:
    :param dt_max:
    :param holiday_list:
    :return:
    """

    start_date = pd.Timestamp(start_date)
    end_date   = pd.Timestamp(end_date)
    my_calendar = determine_calendar_dates(start_date, end_date, delta_max)
    my_dates = select_agency_calendar_dates(my_calendar, holidays)
    print('my dates:{}'.format(my_dates))
    cal_dates = []
    for element in enumerate(my_dates):
        cal_dates.append(my_dates[element].strftime('%Y%m%d'))
    print(cal_dates)

    return cal_dates


def determine_calendar_dates(self, start_date, end_date, delta_max):
    """

    :param start_date:
    :param end_date:
    :param dt_max:
    :return:
    """
    cal = UsaWvCalendar()
    delta = end_date - start_date

    # GTFS feeds can't be > 1 year from start date
    print('{}  days between start and end date.'.format(delta))

    if delta > pd.Timedelta(days=delta_max):
        end_date = pd.DateOffset(days=364) + start_date
        print('   New end date is {}'.format(end_date))
    calendar = cal.holidays(start_date, end_date, return_name=True)
    return calendar

def select_agency_calendar_dates(calendar, holiday_list):
    dates = []
    for index, element in enumerate(calendar.values):
        if calendar.values[element] in holiday_list:
            # print(calendar.index[i], calendar.values[i])
            dates.append(calendar.index[element])
    return dates

class UsaWvCalendar(AbstractHolidayCalendar):
    """
    All the US and Wv holidays my transit agencies may observe.
    """
    rules = [
    Holiday('New Years Day', month=1,  day=1,  observance=nearest_workday),
    USMartinLutherKingJr,
    USPresidentsDay,
    USMemorialDay,
    Holiday('July 4th', month=7,  day=4,  observance=nearest_workday),
    USLaborDay,
    USColumbusDay,
    Holiday('Veterans Day', month=11, day=11, observance=nearest_workday),
    USThanksgivingDay,
    Holiday('Christmas', month=12, day=25, observance=nearest_workday),
    GoodFriday,
    EasterMonday,
    Holiday('Day After Thanksgiving Day', month=11, day=1, offset=DateOffset(weekday=FR(4))),
    Holiday('Veterans Day', month=11, day=11, observance=nearest_workday),
    Holiday('US Election Day', month=11, day=1, observance=election_observance),
    Holiday('WV Primary Election Day', month=5, day=1, observance=election_observance),
    Holiday('WV Day', month=6, day=20),
    ]

def election_observance(dt):
    if dt.year % 2 == 1:
        dt = pd.to_datetime('1/1/2000')
        return dt
    else:
        return dt + pd.DateOffset(weekday=TU(1))