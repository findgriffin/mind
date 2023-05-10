import json


def handler(event, context):
    print(json.dumps(event))
    print(json.dumps(context))
