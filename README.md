# Money-Utils

Automatic reporting system for small clubs analyzing member fees and drink sales.

Monitors money transfers to an account and filters them according to various patterns to report information.

## Features

- Track member fee payments and automatic membership status
- Allows drink account fillup via SEPA bank transfers
- Track expenses and income for drink sales
- Manage member information

## Developer Setup

> **Note**:  
> If all you want is run the service, please head down to the
> **[Deployment](#deployment)** section.

- If you're on Debian, you will need some more packages:

  ```bash
  apt install python3-dev build-essential
  ```

- Enable lingering services for your user:

  ```bash
  sudo loginctl enable-linger $USER
  ```

- Copy `config.example.py` to `config.py` and customize contents according to your likings.
  - insert your account information (`blz`, `user`, `pin`, `iban`)
  - figure out your FinTS information (`product_id` & `fints_url`)
    - https://www.hbci-zka.de/register/prod_register.htm
  - set `bind_host` and `port`
  - set `db_path`
  - for flipdot members: [check teh forumz](TODO)

The following script will:

- Make a virtualenv and install dependencies from [pyproject.toml](pyproject.toml)
- Setup a systemd-user-service `money.service`

  ```bash
  ./setup.sh
  ```

- Make a database:

  ```bash
  mkdir -p data
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

  # or, enable and start the systemd service:
  systemctl --user enable --now money
  ```

- go to http://localhost:5002/ and enjoy the stats!

Deployment in dev setup:

- Edit `uwsgi.ini`

- Run:

  ```bash
  ./manage.py collectstatic
  ./webserver
  ```

## Deployment

Do these steps:

```bash
export SOURCE_COMMIT=$(git describe --always --no-abbrev)
docker-compose build

docker-compose up

## in another window:
docker-compose exec money ./manage.py migrate
docker-compose exec money ./manage.py cratesuperuser
```

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

## License

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

## [member_report.py](member_report.py)

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

Legacy; has been integrated into django app on `/recharges.py`

[webserver](webserver): small flask webserver to do nothing but serve the output of drinks.py as JSON.

Can be started as systemd service, using [money.service](money.service).

---
