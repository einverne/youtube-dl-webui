#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import flask_login

from flask import Flask
from flask import render_template
from flask import request
from flask import flash
from flask import redirect

from multiprocessing import Process
from copy import deepcopy
from .user import User
from .user import UserLoader

MSG = None

app = Flask(__name__)

login_manager = flask_login.LoginManager()
user_loader = UserLoader()

MSG_INVALID_REQUEST = {'status': 'error', 'errmsg': 'invalid request'}


@login_manager.user_loader
def global_user_loader(user_id):
    global user_loader
    return user_loader.get(user_id)


@app.route('/')
@flask_login.login_required
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    if flask_login.current_user.is_authenticated:
        return render_template('index.html')
    else:
        return render_template('login.html')


@app.route('/auth', methods=['POST'])
def auth():
    global user_loader
    payload = request.get_json()
    token_key = payload["token"]

    if app.secret_key == token_key:
        user = User()
        user_loader.add(u'default',user)
        flask_login.login_user(user)
        return redirect('/')

    return render_template('login.html')


@app.route('/task', methods=['POST'])
@flask_login.login_required
def add_task():
    payload = request.get_json()

    MSG.put('create', payload)
    return json.dumps(MSG.get())


@app.route('/task/list', methods=['GET'])
@flask_login.login_required
def list_task():
    payload = {}
    exerpt = request.args.get('exerpt', None)
    if exerpt is None:
        payload['exerpt'] = False
    else:
        payload['exerpt'] = True

    payload['state'] = request.args.get('state', 'all')

    MSG.put('list', payload)
    return json.dumps(MSG.get())


@app.route('/task/state_counter', methods=['GET'])
@flask_login.login_required
def list_state():
    MSG.put('state', None)
    return json.dumps(MSG.get())


@app.route('/task/batch/<action>', methods=['POST'])
@flask_login.login_required
def task_batch(action):
    payload={'act': action, 'detail': request.get_json()}

    MSG.put('batch', payload)
    return json.dumps(MSG.get())

@app.route('/task/tid/<tid>', methods=['DELETE'])
@flask_login.login_required
def delete_task(tid):
    del_flag = request.args.get('del_file', False)
    payload = {}
    payload['tid'] = tid
    payload['del_file'] = False if del_flag is False else True

    MSG.put('delete', payload)
    return json.dumps(MSG.get())


@app.route('/task/tid/<tid>', methods=['PUT'])
@flask_login.login_required
def manipulate_task(tid):
    payload = {}
    payload['tid'] = tid

    act = request.args.get('act', None)
    if act == 'pause':
        payload['act'] = 'pause'
    elif act == 'resume':
        payload['act'] = 'resume'
    else:
        return json.dumps(MSG_INVALID_REQUEST)

    MSG.put('manipulate', payload)
    return json.dumps(MSG.get())


@app.route('/task/tid/<tid>/status', methods=['GET'])
@flask_login.login_required
def query_task(tid):
    payload = {}
    payload['tid'] = tid

    exerpt = request.args.get('exerpt', None)
    if exerpt is None:
        payload['exerpt'] = False
    else:
        payload['exerpt'] = True

    MSG.put('query', payload)
    return json.dumps(MSG.get())


@app.route('/config', methods=['GET', 'POST'])
@flask_login.login_required
def get_config():
    payload = {}
    if request.method == 'POST':
        payload['act'] = 'update'
        payload['param'] = request.get_json()
    else:
        payload['act'] = 'get'

    MSG.put('config', payload)
    return json.dumps(MSG.get())


###
# test cases
###
@app.route('/test/<case>')
@flask_login.login_required
def test(case):
    return render_template('test/{}.html'.format(case))


class Server(Process):
    def __init__(self, msg_cli, conf):
        super(Server, self).__init__()

        self.msg_cli = msg_cli

        self.host = conf['server']['host']
        self.port = conf['server']['port']
        self.secret_key = conf['general']['login_secret_key']

    def run(self):

        global MSG
        MSG = self.msg_cli

        app.secret_key = self.secret_key
        login_manager.login_view = '/login'
        login_manager.init_app(app)

        app.run(host=self.host, port=int(self.port), use_reloader=False)


