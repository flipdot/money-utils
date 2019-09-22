
# check https://www.hbci-zka.de/institute/institut_auswahl.htm
# https://www.willuhn.de/wiki/doku.php?id=support:list:banken
# https://www.homebanking-hilfe.de/forum/topic.php?t=1174
# to find your url
# Kasseler Sparkasse: https://banking-hs3.s-fints-pt-hs.de/fints30
fints_url = "http://FILL_ME"

# Kasseler Sparkasse: 52050353
blz = "BLZ"
user = "USERNAME"
pin = "" # leave empty to ask
iban = "DE0000000000000"
product_id = "FILL_ME"

load_interval_minutes = 60

bind_host = '127.0.0.1'
port = 5002
flask_debug = True

db_path = "money.sqlite"

debug = False

# number of days to shift month boundary
# used to mark payments coming on the 29th for the next month
crossover_days = 10

# We ignore transactions that are not within the requested time frame.
# allow some fuzz time in case the bank does not know how to math
import_fuzz_grace_days = 2
