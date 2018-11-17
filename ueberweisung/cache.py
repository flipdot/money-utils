import logging
import os
import pickle

save_path = "cache.bin"
cache = None

def load_cache():
    global cache
    if cache:
        return cache
    if os.path.exists(save_path):
        with open(save_path, "rb") as fd:
            cache = pickle.load(fd, encoding="UTF8")
            logging.info("Loaded %d txs from cache.", len(cache['txs']))
    else:
        cache = {'txs': {}}
    return cache

def save_cache():
    global cache
    with open(save_path, "wb") as fd:
        pickle.dump(cache, fd)