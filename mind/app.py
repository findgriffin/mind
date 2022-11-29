#!/usr/bin/env python
from flask import Flask, jsonify, request, Response, send_from_directory, \
    render_template

from mind import DEFAULT_DB, QueryStuff, Mind, Order, PAGE_SIZE, Phase, \
    add_content, do_tick, update_state, Stuff

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


@app.route('/', methods=['POST'])
def index():
    mnd = Mind(DEFAULT_DB)
    if QUERY in request.json:
        query = request.json[QUERY]
        order = Order[query[ORDER]] if ORDER in query else Order.LATEST
        page = int(query[PAGE]) if PAGE in query else 1
        num = int(query[NUM]) if NUM in query else PAGE_SIZE + 1
        phase = Phase[query[PHASE]] if PHASE in query else Phase.ACTIVE
        tag = query[TAG] if TAG in query and query[TAG].isalnum() else None
        return jsonify(QueryStuff(order=order, offset=(page - 1) * num,
                                  state=phase, tag=tag).fetchall(mnd))
    elif ADD in request.json:
        stuff, tags = add_content(mnd, request.json[ADD])
        return jsonify({'tags': [t.tag for t in tags]})
    elif TICK in request.json:
        stf = Stuff(request.json[TICK]['id'], "", state=Phase.ACTIVE)
        return jsonify({'updated': update_state(stf, mnd, Phase.DONE)})
    elif UNTICK in request.json:
        stf = Stuff(request.json[UNTICK]['id'], "", state=Phase.DONE)
        return jsonify({'updated': update_state(stf, mnd, Phase.ACTIVE)})
    else:
        return Response(400)


app.run()
