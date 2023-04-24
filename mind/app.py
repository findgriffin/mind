#!/usr/bin/env python
import json

from flask import Flask, jsonify, request, Response, send_file, \
    render_template, make_response, redirect, url_for  # type: ignore
from werkzeug.exceptions import HTTPException

from mind import DEFAULT_DB, Epoch, QueryStuff, Mind, Order, PAGE_SIZE, Phase,\
    add_content, setup_logging, update_state, Stuff

app = Flask(__name__, static_url_path="", static_folder="../static")

ADD = 'add'
NUM = 'num'
ORDER = 'order'
PAGE = 'page'
PHASE = 'phase'
QUERY = 'query'
TAG = 'tag'
TICK = 'tick'
UNTICK = 'untick'


def handle_query(mnd, query):
    order = Order[query[ORDER]] if ORDER in query else Order.LATEST
    page = int(query[PAGE]) if PAGE in query else 1
    num = int(query[NUM]) if NUM in query else PAGE_SIZE + 1
    phase = Phase[query[PHASE]] if PHASE in query else Phase.ACTIVE
    tag = query[TAG] if TAG in query and query[TAG].isalnum() else None
    return jsonify(QueryStuff(order=order, offset=(page - 1) * num,
                              state=phase, tag=tag).fetchall(mnd))


@app.get('/')
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
