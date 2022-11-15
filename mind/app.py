#!/usr/bin/env python
from argparse import Namespace

from flask import Flask, jsonify, request

from mind import QueryStuff, Mind, Order, PAGE_SIZE, Phase
import mind

app = Flask(__name__)

ADD = ''
NUM = 'num'
ORDER = 'order'
PAGE = 'page'
PHASE = 'phase'
QUERY = 'query'
TAG = 'tag'


@app.route('/', methods=['GET', 'POST'])
def index():
    mnd = Mind(mind.DEFAULT_DB)
    if QUERY in request.json:
        query = request.json[QUERY]
        order = Order[query[ORDER]] if ORDER in query else Order.LATEST
        page = int(query[PAGE]) if PAGE in query else 1
        num = int(query[NUM]) if NUM in query else PAGE_SIZE + 1
        phase = Phase[query[PHASE]] if PHASE in query else Phase.ACTIVE
        tag = query[TAG] if TAG in query and query[TAG].isalnum() else None
        return jsonify(QueryStuff(order=order, offset=(page - 1) * num,
                                  state=phase, tag=tag).fetchall(mnd))


app.run()
