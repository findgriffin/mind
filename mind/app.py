#!/usr/bin/env python
import json

from dataclasses import dataclass
from flask_login import login_user, LoginManager, UserMixin, \
    login_required, logout_user
from flask import Flask, jsonify, request, Response, send_file, \
    render_template, make_response, redirect, url_for  # type: ignore
from typing import Optional
from werkzeug.exceptions import HTTPException

from mind import DEFAULT_DB, Epoch, QueryStuff, Mind, Order, PAGE_SIZE, Phase,\
    add_content, setup_logging, update_state, Stuff

app = Flask(__name__, static_url_path="")
app.secret_key = 'dev'
app.config.from_object('config')

login_manager = LoginManager(app)
login_manager.login_view = 'serve_login'

ADD = 'add'
NUM = 'num'
ORDER = 'order'
PAGE = 'page'
PHASE = 'phase'
QUERY = 'query'
TAG = 'tag'
TICK = 'tick'
UNTICK = 'untick'


@dataclass
class User(UserMixin):
    id: str
    password: str
    salt: str

USERS = {
    'davo': User(id='davo', password='str1ke', salt='bar')
}


@login_manager.user_loader
def load_user(user_id) -> Optional[str]:
    return USERS[user_id] if user_id in USERS else None



def handle_query(mnd, query):
    order = Order[query[ORDER]] if ORDER in query else Order.LATEST
    page = int(query[PAGE]) if PAGE in query else 1
    num = int(query[NUM]) if NUM in query else PAGE_SIZE + 1
    phase = Phase[query[PHASE]] if PHASE in query else Phase.ACTIVE
    tag = query[TAG] if TAG in query and query[TAG].isalnum() else None
    return jsonify(QueryStuff(order=order, offset=(page - 1) * num,
                              state=phase, tag=tag).fetchall(mnd))


@app.route('/login', methods=['POST'])
def handle_login():
    app.logger.info(f'handling {request.form}')
    app.logger.info(f'handling {request.form.keys()}')
    if 'user' in request.form and 'password' in request.form:
        user_id = request.form['user']
        if user_id in USERS:
            user = USERS[user_id]
            if request.form['password'] == user.password:
                app.logger.info(f'logging in {user_id}')
                login_user(user=user, remember=True)
                return redirect('/')
    return redirect('error?code=401')


@app.get('/login')
def serve_login():
    return send_file('../static/login.html')

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    logout_user()
    return redirect('/login')

@app.get('/')
@login_required
def serve_index():
    return send_file('../static/index.html')


@app.get('/error')
def serve_error():
    return send_file('../static/error.html')


@app.errorhandler(HTTPException)
def handle_errors(error):
    app.logger.warning(f'Handling {error.code}: {error.name}')
    return redirect(f'error?code={error.code}')


@app.route('/', methods=['POST'])
@login_required
def handle_index():
    mnd = Mind(DEFAULT_DB)
    app.logger.info(f'Processing request: {json.dumps(request.json)}')
    if QUERY in request.json:
        return handle_query(mnd, request.json[QUERY])
    elif ADD in request.json:
        stuff, tags = add_content(mnd, request.json[ADD])
        return jsonify({'tags': [t.tag for t in tags], 'stuff': stuff})
    elif TICK in request.json:
        stf = Stuff(Epoch(request.json[TICK]['id']),
                    request.json[TICK]['body'], state=Phase.ACTIVE)
        return jsonify({'updated': update_state(stf, mnd, Phase.DONE)})
    elif UNTICK in request.json:
        stf = Stuff(Epoch(request.json[UNTICK]['id']),
                    request.json[TICK]['body'], state=Phase.DONE)
        return jsonify({'updated': update_state(stf, mnd, Phase.ACTIVE)})
    else:
        return Response(400)


if __name__ == '__main__':
    setup_logging(True)
    app.run()
