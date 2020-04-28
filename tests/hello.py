#!/usr/bin/env python

from flask import Flask, send_from_directory
from flask_cors import CORS
import logging


app = Flask(__name__, static_url_path='')
CORS(app)

logging.getLogger('flask_cors').level = logging.DEBUG


@app.route('/')
def hello_world():
    return app.send_static_file('websockets_test.html')


if __name__ == '__main__':
    app.run(debug=True)
