import enum
import re


class PayInterval(enum.Enum):
    MONTHLY = 1
    SIX_MONTH = 2
    YEARLY = 3
    VARIABLE = 4

class CommonFee(enum.Enum):
    STUDENT = 10
    REGULAR = 23
    SUPPORTER = 36

class AllFee(enum.Enum):
    STUDENT = 10
    REGULAR = 23
    SUPPORTER = 36

    SYMBOLIC = 1
    REDUCED_3 = 3
    REDUCED_5 = 5
    STUDENT_15 = 15
    REGULAR_18 = 18

class DetectMethod(enum.IntEnum):
    MANUAL = 100
    FEE_COMMAND = 90
    
    LAST_FEE = 20
    MULTIPLE_OF_FEE = 10

    FALLBACK = 0

common_fee_amounts = {f.value: f.name for f in CommonFee}
fee_amounts = {f.value: f.name for f in AllFee}

d = lambda name, num: r'(?P<%s>\d{%d})' % (name, num)

space_or_start = r'(?:^|\s)'
space_or_end = r'(?=$|\s)'

iso_ym = lambda suffix: d('year'+suffix, 4) + r'-' + d('month'+suffix, 2)

month_regex_ymd_range = re.compile(space_or_start + iso_ym('_start') + r'\s-\s'+ iso_ym('_end') + space_or_end)

month_regex_ymd = re.compile(space_or_start + iso_ym('') + space_or_end)
month_regex_ym = re.compile(space_or_start + d('month', 2) + r'/' + d('year', 4) + space_or_end)
