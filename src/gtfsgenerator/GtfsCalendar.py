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

def ServiceExceptions(configs, holiday_list):
    """

    :param configs:
    :return:
    """

    start_date = configs.feed_start_date
    end_date   = configs.feed_end_date
    delta_max  = configs.delta_max
    holiday_list
    # TODO 'process' the holiday text to remove white space and apostrophes
    if not start_date:
        print(colored('No start date, assuming today.', 'red'))
        start_date = pd.datetime.today().strftime('%Y%m%d')
    if not end_date:
        print(colored('No end date.', 'red'))
        end_date   = start_date + DateOffset(days=364)
    if not delta_max:
        print(colored('No maximun feed length (days) specified.', 'red'))
    if not holiday_list:
        print(colored('No holidays specified.', 'red'))

    cal_dates = getDates(start_date, end_date, delta_max, holiday_list)

    return cal_dates


def getDates(start, end, delta_max, holidays):
    """

    :param begin_date:
    :param end:
    :param dt_max:
    :param holiday_list:
    :return:
    """

    start = pd.Timestamp(start)
    end   = pd.Timestamp(end)

    print('from getDates start:{} end:{} dt:{}'.format(start, end, delta_max))
    my_calendar = determine_calendar_dates(start, end, delta_max)
    print('from getDates my_calendar\n{}'.format(vars(my_calendar)))
    my_dates = select_agency_calendar_dates(my_calendar, holidays)

    print('my dates:{}'.format(my_dates))

    cal_dates = []
    for index, date in enumerate(my_dates):
        print('  >> date {}: {}'.format(index, date.strftime('%Y%m%d')))

    print(cal_dates)

    return cal_dates


def determine_calendar_dates(start_date, end_date, delta_max):
    """
    This function determines all the holidays defined in the USA-WV Calendar class between the start and end dates.
    :param start_date:
    :param end_date:
    :param dt_max:
    :return:
    """
    cal = UsaWvCalendar()
    delta = end_date - start_date
    print('   end_date {} - start_date {} = delta {}'.format(end_date, start_date, delta))

    # GTFS feeds can't be > 1 year from start date
    print('{}  days between start and end date.'.format(delta))

    if delta > pd.Timedelta(days=int(delta_max)):
        end_date = DateOffset(days=364) + start_date
        print('   New end date is {}'.format(end_date))
    calendar = cal.holidays(start_date, end_date, return_name=True)
    return calendar


def select_agency_calendar_dates(calendar, holiday_list):
    dates = []
    print(calendar)
    for index, day in enumerate(calendar):
        print('From all holidays index:{} day:{}'.format(index, day))
        if calendar.values[index] in holiday_list:
            print(' >>> my date:{}  my holiday:{}'.format(calendar.index[index].strftime('%Y%m%d'), calendar.values[index]))
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