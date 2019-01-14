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


common_fee_amounts = {f.value: f.name for f in CommonFee}
fee_amounts = {f.value: f.name for f in AllFee}

month_regex = re.compile(r'(?:^|\s)(?P<year>\d{4})-(?P<month>\d{2})(?=$|\s)')
