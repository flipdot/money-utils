import pickle

from fints.client import NeedTANResponse
from money_utils.utils import load_pickle, save_pickle
from money_utils.bank.utils import ask_for_tan

from fints.utils import minimal_interactive_cli_bootstrap
from fints.client import FinTS3PinTanClient


def create_client_from_config(config):
    client = FinTS3PinTanClient(
        config["bank_identifier"],
        config["user_id"],
        config["pin"],
        config["server"],
        product_id=config["product_id"],
    )
    if config["tan_mechanism"] is not None:
        client.fetch_tan_mechanisms()
        client.set_tan_mechanism(config["tan_mechanism"])
    minimal_interactive_cli_bootstrap(client)
    return client


def load_client_from_config(config):

    # fixes
    # https://github.com/raphaelm/python-fints/issues/158
    # by hints from
    # https://github.com/raphaelm/python-fints/issues/174

    data, system_id = load_pickle(config["client_state_file_location"])

    client = FinTS3PinTanClient(
        config["bank_identifier"],
        config["user_id"],
        config["pin"],
        config["server"],
        product_id=config["product_id"],
        from_data=data,
        system_id=system_id,
    )
    client.selected_tan_medium = ''
    minimal_interactive_cli_bootstrap(client)
    return client


def client_from_config(config, tan_callback=None, force_creation=False):
    if force_creation:
        client = create_client_from_config(config)
    else:
        try:
            client = load_client_from_config(config)
        except FileNotFoundError as err:
            print(err)
            client = create_client_from_config(config)
    with client:
        if tan_callback is None:
            tan_callback = ask_for_tan
        while isinstance(client.init_tan_response, NeedTANResponse):
            client.init_tan_response = ask_for_tan(client, client.init_tan_response)
    return client


def save_client_with_config(client, config):
    if client:
        data = client.deconstruct(True)
        save_pickle(config["client_state_file_location"], (data, client.system_id))

