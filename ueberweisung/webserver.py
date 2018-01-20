#!?usr/bin/env python3
import flask
from flask_compress import Compress

import config
import drinks

app = flask.Flask(__name__)
Compress(app)

@app.route('/')
def index():
    return flask.redirect("/recharges.json", 302)

@app.route('/recharges.json')
def recharges():
    all = drinks.load_recharges()
    return flask.jsonify(all)

if __name__ == "__main__":
    app.run(
        host=config.bind_host,
        debug=config.flask_debug,
        port=config.port
    )
