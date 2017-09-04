import sys
sys.path.append('..')

import datetime
from easyweb import run, route, render_template

@route('/')
def index():
    return 'Welcome to EasyWeb!'


@route('/hello')
def hello():
    return 'Hello Stranger!'

@route('/now')
def now():
    now = datetime.datetime.now()
    return str(now)

@route('/showname/:name')
def showname(name):
    return 'this is your name:' + name

@route('/index')
def index():
    return render_template('index.html')


run(host='0.0.0.0', port=8000)
