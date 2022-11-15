#!/usr/bin/env python
from argparse import Namespace

from flask import Flask, jsonify, request

import mind

app = Flask(__name__)

QUERY = 'query'


@app.route('/', methods=['POST'])
def index():
    if QUERY in request.json:
        return jsonify(mind.QueryStuff(**request.json[QUERY]))
    if 'list' in request.json:
        result = mind.list_inner(mind.Mind(mind.DEFAULT_DB),
                                 Namespace(**request.json['list']))
        return jsonify([mind.Stuff(*r).preview() for r in result])


app.run()
