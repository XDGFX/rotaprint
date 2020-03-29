#!/usr/bin/env python
from flask import Flask, escape, request

app = Flask(__name__)


@app.route('/')
def index():
    return app.send_static_file('index.html')


if __name__ == '__main__':
    app.run(debug=True)
