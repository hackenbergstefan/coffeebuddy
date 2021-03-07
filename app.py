from flask import Flask, url_for, render_template

app = Flask(__name__)


@app.route('/')
def hello():
    return render_template('coffee.html')
