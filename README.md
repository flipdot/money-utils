# Money-Utils

Monitors money transfers to an account and filters them according to various patterns to report information.

## Setup
- Copy `config.example.py` to `config.py` and customize contents according to your likings.

- Make a virtualenv and install dependencies from [requirements.txt](requirements.txt)
```bash
./setup.sh
```

- Make a database:
```bash
./manage.py migrate
./manage.py createsuperuser
```

- Run Cron jobs to import TXs
  - this will:
    - import transactions from your bank
    - analyze member fees
```bash
./manage.py runcrons
```

- Start server:
```bash
./manage.py runserver
```

- go to http://localhost:8000/ and enjoy the stats!

## Member Management
Once the server is running, go to http://localhost:8000/admin.
Log in, and click on "Members".
Add some members. The only fields you will have to fill out:

- First Name
- Last Name (if you know it)
- Nickname (if you know it)
- Email (if you know it)
- Fee (if it isn't one of the standard fees from [fee_util.py](schema/fee_util.py))

These properties will be used to find the member fee transactions.
All the other fields will be filled by the analysis.

After adding some members, do `./manage.py runcrons` again to analyze their fees.

# License
GPLv3. Other licenses available upon request.

---
---

# BELOW LEGACY

## `/recharges.json`
Lists drinks-recharge events according to the pattern `drinks <uid> <info>`, where
- uid is the LDAP user ID
- info is some additional text, commonly "username random-string"

The random string at the end is used to differentiate recharges happening on the same day, since SEPA does not generate unique transaction IDs.
Instead, it considers the 5-tuple (date, IBAN from, IBAN to, amount, transaction text) as unique key.

## [load_transactions.py](load_transactions.py)

loads new transactions from the bank.

## [members.py](members.py)

performs member fee analysis.

## [report.py](report.py)

displays an oldschool ASCII report of paid member fees in the last 12 months.

## [clear_analysis.py](clear_analysis.py)

clears all analyzed data from database (except for Fee_Entries).
Can be used to rescue the database from botched data if you're messing with the [members.py](members.py) script.

## [hbci_client.py](hbci_client.py)

Wrapper for the python-fints library.


---
Old stuff:

## [drinks.py](drinks.py)

old report: loads transactions and drinks-recharges using an ad-hoc pickle cache defined in [cache.py](cache.py).

[cache_to_db.py](cache_to_db.py) can be used to migrate data from that cache structure into the sqlite database. No guarantees.

Legacy; has been integrated into django app on `/recharges.py`

[webserver.py](webserver.py): small flask webserver to do nothing but serve the output of drinks.py as JSON.

Can be started as systemd service, using [money.service](money.service).

---
