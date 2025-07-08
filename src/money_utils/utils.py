import pickle
import os
from datetime import date
from typing import Iterator

from dotenv import dotenv_values
from omegaconf import OmegaConf
from dateutil.relativedelta import relativedelta


def months(from_date: date, to_date: date) -> Iterator[date]:
    from_month = from_date.replace(day=1)
    to_month = to_date.replace(day=1)

    while from_month <= to_month:
        next = from_month + relativedelta(months=+1)
        yield from_month, next
        from_month = next


months_german = {
    "Januar": 1,
    "Februar": 2,
    "Maerz": 3,
    "April": 4,
    "Mai": 5,
    "Juni": 6,
    "Juli": 7,
    "August": 8,
    "September": 9,
    "Oktober": 10,
    "November": 11,
    "Dezember": 12,
}


CONFIG_DEFAULTS = {
    "debug": True,
    "tan_mechanism": None,
    "django_secret_key": None,
}

def map_to_builtin(value):
    if not isinstance(value, str):
        return value

    normalized = value.strip().lower()

    if normalized == "true":
        return True
    elif normalized == "false":
        return False
    elif normalized == "none":
        return None

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value


def get_config(config_defaults=None, config_key="money_utils__", update_env=None):
    if config_defaults is None:
        config_defaults = CONFIG_DEFAULTS
    env_config = {
        **dotenv_values(".default.env"),  # load shared development variables
        **dotenv_values(".env"),  # load sensitive variables
        **os.environ,  # override loaded values with environment variables
    }
    env_config = {
        k[len(config_key) :].lower(): v
        for k, v in env_config.items()
        if k.startswith(config_key.upper())
    }
    config = {**config_defaults, **env_config}
    if update_env is not None:
        def _update_env(k, v):
            k_ = config_key.upper() + k.upper()
            os.environ[k_] = v

        if isinstance(update_env, bool) and update_env:
            for k, v in config.items():
                _update_env(k, v)
        elif isinstance(update_env, str):
            v = config[update_env]
            _update_env(update_env, v)
        elif isinstance(update_env, list):
            for k in update_env:
                v = config[k]
                _update_env(k, v)
        else:
            raise NotImplementedError((update_env, type(update_env)))
    for k in list(config.keys()):
        if k in ["debug", "load_interval_minutes", "crossover_days", "import_fuzz_grace_days", "report_month_end"]:
            config[k] = map_to_builtin(config[k])
    config = OmegaConf.create(config)
    return config


def load_pickle(location):
    with open(location, "rb") as fd:
        return pickle.load(fd)


def save_pickle(location, obj):
    with open(location, "wb") as fd:
        pickle.dump(obj, fd)

