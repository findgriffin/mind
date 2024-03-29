#!/usr/bin/env python
import os
import secrets
from dataclasses import dataclass
from sqlite3 import IntegrityError, Connection

import sqlite3
# type: ignore
from flask_login import login_user, LoginManager, UserMixin, \
    login_required, logout_user, current_user, encode_cookie, decode_cookie
from flask import Flask, jsonify, request, Response, send_file, \
    render_template, redirect  # type: ignore
from typing import Optional

from pathlib import Path
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash, check_password_hash

import json

from mind import DEFAULT_DB, Epoch, QueryStuff, Mind, Order, PAGE_SIZE, \
    Phase, add_content, setup_logging, update_state, Stuff, QueryTags


def create_app():
    return Flask(__name__, static_url_path='')


app = create_app()
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

login_manager = LoginManager(app)
login_manager.login_view = 'serve_login'

USERS_DB = 'users.db'

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
    secret: str

    @classmethod
    def create(cls, name: str, password: str):
        hash = generate_password_hash(password)
        return cls(name, hash)


def init_db() -> tuple[Connection, bool]:
    """Returns True if the DB was initialized."""
    path: Optional[Path] = None
    if app.config.get('TESTING', False):
        exists = False
    else:
        path = Path(USERS_DB).expanduser()
        exists = path.exists() and path.stat().st_size > 0
        app.logger.debug(f"Opening DB {path}, exists: {path.exists()}")
    con = sqlite3.connect(path or ':memory:')
    if exists:
        row = con.execute('SELECT COUNT(*) FROM users').fetchone()
        return con, row[0] > 0
    else:
        con.execute('CREATE TABLE users('
                    'id TEXT PRIMARY KEY NOT NULL, '
                    'secret TEXT NOT NULL)')
        con.execute('CREATE TABLE tokens(token TEXT PRIMARY KEY NOT NULL)')
        con.commit()
    return con, exists


def get_db() -> Connection:
    path = ':memory:' if app.config.get('TESTING', False) else USERS_DB
    return sqlite3.connect(path)


def add_user(user: User, token: Optional[str]) -> bool:
    con, exists = init_db()
    with con:
        try:
            con.execute('INSERT INTO users (id, secret) VALUES (?, ?)',
                        (user.id, user.secret))
            if token:
                con.execute('DELETE FROM tokens WHERE token = ?', (token,))
            return True
        except IntegrityError:
            app.logger.warning(f'User {user.id} already exists.')
            return False


def add_token() -> str:
    con, exists = init_db()
    with con:
        token = secrets.token_hex()
        con.execute('INSERT INTO tokens (token) VALUES (?)', (token,))
        return token


def init_mind() -> Mind:
    return Mind(':memory:' if app.config.get('TESTING', False) else DEFAULT_DB)


@login_manager.user_loader
def load_user(user_id) -> Optional[User]:
    try:
        con, exists = init_db()
        with con:
            cur = con.execute('SELECT * from users where id = ?', (user_id,))
            row = cur.fetchone()
            return User(*row) if row else None
    except Exception as err:
        app.logger.warning(f'Exception loading user {err}')
        return None


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
        user = load_user(request.form['user'])
        if user:
            if check_password_hash(user.secret, request.form['password']):
                app.logger.info(f'logging in {user.id}')
                login_user(user=user, remember=True)
                return redirect('/')
    return redirect('error?code=401')


@app.get('/login')
def serve_login():
    con, exists = init_db()
    if exists:
        if current_user.is_authenticated:
            return redirect('/logout')
        else:
            return render_template('login.html')
    else:
        return redirect(f'/register/{encode_cookie(add_token())}')


@app.get('/logout')
@login_required
def serve_logout():
    return render_template('logout.html', user=current_user)


@app.route('/logout', methods=['POST'])
def logout():
    logout_user()
    return redirect('/login')


@app.get('/register')
@login_required
def serve_add_user():
    return redirect(f'/register/{encode_cookie(add_token())}')


@app.get('/register/<token>')
def serve_register(token):
    app.logger.info(f'Registering token: {token}')
    return render_template('register.html', token=token)


@app.route('/register', methods=['POST'])
def handle_register():
    if all(key in request.form for key in ['user', 'token', 'password']):
        user_name = request.form['user']
        token = request.form['token']
        decoded = decode_cookie(request.form['token'])
        if decoded:
            app.logger.info(f'Decoded cookie {decoded}')
            new_user = User.create(user_name, request.form['password'])
            if add_user(new_user, token):
                login_user(new_user, remember=True)
                return redirect('/')
            else:
                return redirect('/error?code=409')
        else:
            app.logger.info('could not decode cookie')
    else:
        app.logger.warning('Missing field')
    return redirect('error?code=401')


@app.get('/')
@login_required
def serve_index():
    return render_template('index.html', user=current_user)


@app.get('/error')
def serve_error():
    return send_file('static/error.html')


@app.errorhandler(HTTPException)
def handle_errors(error):
    app.logger.warning(f'Handling {error.code}: {error.name}')
    return redirect(f'error?code={error.code}')


@app.route('/stuff', methods=['POST'])
@login_required
def handle_stuff():
    mnd = init_mind()
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
                    request.json[UNTICK]['body'], state=Phase.DONE)
        return jsonify({'updated': update_state(stf, mnd, Phase.ACTIVE)})
    else:
        return Response(400)


@app.route('/tags', methods=['POST'])
@login_required
def handle_tags():
    return jsonify(QueryTags(None, limit=3).execute(init_mind()))


if __name__ == '__main__':
    setup_logging(True)
    app.run()
