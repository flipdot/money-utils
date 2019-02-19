# Ueberweisung
Monitors money transfers to an account and filters them according to various patterns to save information.

## Setup
Copy `config.example.py` to `config.py` and customize contents according to your likings.




# BELOW LEGACY

## output
start as systemd service, using `money.service`
The systemd service starts a webserver with the following endpoints:

### `/recharges.json`
Lists drinks-recharge events according to the pattern `drinks <uid> <info>`, where
- uid is the LDAP user ID
- info is some additional text, commonly "username random-string"

The random string at the end is used to differentiate recharges happening on the same day, since SEPA does not generate unique transaction IDs.
Instead, it considers the 5-tuple (date, IBAN from, IBAN to, amount, transaction text) as unique key.
