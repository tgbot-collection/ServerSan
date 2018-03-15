#!/usr/bin/python
# coding:utf-8

# ServerSan - webhook.py
# 2018/3/15 11:08
#

__author__ = 'Benny <benny@bennythink.com>'
import json
import time

import pymongo
from flask import Flask, request

client = pymongo.MongoClient()
db = client['ServerSan']
col = db['sysinfo']

app = Flask(__name__)


@app.route("/v1/create", methods=['POST'])
def hello():
    try:
        d = json.loads(request.data)
    except ValueError:
        return json.dumps({'status': 1, 'info': 'request failed.'})

    current_ts = time.time()
    _id = False
    d.update(timestamp=current_ts)

    perm = can_insert(d.get('auth'), current_ts)
    if perm:
        _id = col.insert_one(d).inserted_id
    if _id:
        return json.dumps({'status': 0, 'info': 'success'})
    else:
        return json.dumps({'status': 2, 'info': 'database failed: operation too frequent.'})


def can_insert(auth_code, current_ts):
    db_ts = 0
    for i in col.find({'auth': auth_code}).sort('timestamp', pymongo.DESCENDING):
        db_ts = i['timestamp']
        break

    return True if current_ts - db_ts >= 180 else False


if __name__ == '__main__':
    app.run(host='0.0.0.0')
