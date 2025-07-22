from util import load_pickle, save_pickle
# from money_utils.bank.utils import ask_for_tan

from fints.utils import minimal_interactive_cli_bootstrap
from fints.client import FinTS3PinTanClient

import config

import logging

fints_logger = logging.getLogger("fints.client")
fints_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

def create_client_from_config():
    client = FinTS3PinTanClient(
        config.blz,
        config.user,
        config.pin,
        config.fints_url,
        product_id=config.product_id,
    )
    if config.tan_mechanism:
        client.fetch_tan_mechanisms()
        client.set_tan_mechanism(config.tan_mechanism)
    minimal_interactive_cli_bootstrap(client)
    return client


def load_client_from_config():

    # fixes
    # https://github.com/raphaelm/python-fints/issues/158
    # by hints from
    # https://github.com/raphaelm/python-fints/issues/174

    data, system_id = load_pickle(config.client_state_file_location)

    client = FinTS3PinTanClient(
        config.blz,
        config.user,
        config.pin,
        config.fints_url,
        product_id=config.product_id,
        from_data=data,
        system_id=system_id,
    )
    client.selected_tan_medium = ''
    minimal_interactive_cli_bootstrap(client)
    return client


def client_from_config(tan_callback=None, force_creation=False):
    from hbci_client import terminal_tan_callback

    if force_creation:
        client = create_client_from_config()
    else:
        try:
            client = load_client_from_config()
        except FileNotFoundError as e:
            logger.info("State not recovered: %s", e)
            client = create_client_from_config()
    with client:
        if tan_callback is None:
            tan_callback = terminal_tan_callback
        if client.init_tan_response:
            logging.info("Calling tan callback for init_tan_response %s", client.init_tan_response)
            tan = tan_callback(client.init_tan_response)
            client.send_tan(client.init_tan_response, tan)
    return client


def save_client(client):
    if client:
        data = client.deconstruct(True)
        save_pickle(config.client_state_file_location, (data, client.system_id))

