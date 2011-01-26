from datetime import date, timedelta

# Requirements:
# * Convert from an ox date to a normal date                ox_to_normal
# * Convert from a normal date to an ox date                normal_to_ox
# * Find the most recent start-of-term for a given date     term_start
# * Convert a (year, term) pair to a string                 term_as_string
# * Convert a string to a (year, term) pair                 term_from_string
# * Prettyprint a (year, term) pair                         get_term_display

TERM_NAMES = {
    1: 'Hilary',
    2: 'Trinity',
    3: 'Michaelmas',
}

TERM_NAMES_INV = {
    'h': 1, 'Hilary': 1,
    't': 2, 'Trinity': 2,
    'm': 3, 'Michaelmas': 3,
}

TERM_LETTERS = {
    1: 'h',
    2: 't',
    3: 'm',
}

TERM_STARTS = {
    (2007, 3): date(2007,  9, 30),
    (2008, 1): date(2008,  1,  6),
    (2008, 2): date(2008,  4, 13),
    (2008, 3): date(2008, 10,  5),
    (2009, 1): date(2009,  1, 11),
    (2009, 2): date(2009,  4, 19),
    (2009, 3): date(2009, 10,  4),
    (2010, 1): date(2010,  1, 10),
    (2010, 2): date(2010,  4, 18),
    (2010, 3): date(2010, 10,  3),
    (2011, 1): date(2011,  1,  9),
    (2011, 2): date(2011,  4, 24),
    (2011, 3): date(2011, 10,  2),
    (2012, 1): date(2012,  1, 18),
    (2012, 2): date(2012,  4, 15),
}

OFFSET_TERM_STARTS = dict((k,v-timedelta(14)) for k,v in TERM_STARTS.items())

DAY_NAMES = [
    'Sunday', 'Monday', 'Tuesday', 'Wednesday',
    'Thursday', 'Friday', 'Saturday'
]

TERM_STARTS_LIST = sorted(TERM_STARTS.items())
OFFSET_TERM_STARTS_LIST = sorted(OFFSET_TERM_STARTS.items())

def get_term_display(s):
    return "%s %s" % (TERM_NAMES[int(s[4])], s[:4])

def term_as_string(year = None, term = None):
    if year is None:
        year, term = term_start()
    return "%d%d" % (year, term)

def term_start(pdate=None):
    if pdate is None:
        pdate = date.today()
    for i in range(1, len(OFFSET_TERM_STARTS_LIST)):
        if OFFSET_TERM_STARTS_LIST[i-1][1] <= pdate and OFFSET_TERM_STARTS_LIST[i][1] > pdate:
            break
    return OFFSET_TERM_STARTS_LIST[i-1][0]

def ox_to_normal(year, term, week = 0, day = 0):
    return TERM_STARTS[(year, term)] + timedelta(week*7+day)

def normal_to_ox(pdate):
    year, term = term_start(pdate)
    week, day = divmod((pdate - OFFSET_TERM_STARTS[(year, term)] - timedelta(14)).days, 7)
    return (year, term, week, day)
    
def ox_date_dict(dt=None):
    dt = dt.date() if dt else date.today()
    year, term, week, day = normal_to_ox(dt)
    return {
        'day_name': DAY_NAMES[day],
        'day': day,
        'week': week,
        'ordinal': 'th' if 10<week<20 else {1:'st',2:'nd',3:'rd'}.get(abs(week)%10, 'th'),
        'term': term,
        'term_short': TERM_LETTERS[term].upper(),
        'term_long': TERM_NAMES[term],
        'year': year,
        'day_number': dt.day,
        'month': dt.strftime('%b'),
    }

def format_today():
    return "%(day_name)s, %(week)d%(ordinal)s week, %(term_long)s %(year)d (%(day_number)d %(month)s)" % ox_date_dict()
    return "%(day_name)s, %(day_number)d %(month)s %(year)d" % ox_date_dict()
