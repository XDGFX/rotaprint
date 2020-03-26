from flask import Flask, send_from_directory
app = Flask(__name__, static_url_path='')


@app.route('/')
def hello_world():
    return app.send_static_file('db_test.html')


if __name__ == '__main__':
    app.run(debug=True)
