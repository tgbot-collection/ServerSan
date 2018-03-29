#!/usr/bin/python
# coding:utf-8

# ServerSan - webhook.py
# 2018/3/15 11:08
#

__author__ = 'Benny <benny@bennythink.com>'
__version__ = '1.0.0'

import json
import time

import pymongo
from flask import Flask, request

client = pymongo.MongoClient()
db = client['ServerSan']
col = db['sysinfo']

app = Flask(__name__)


@app.route("/")
def index():
    return json.dumps({'status': 0, 'info': 'This is ServerSan\'s index API.'})


@app.route("/v1/create", methods=['POST'])
def create():
    try:
        d = json.loads(request.data)
    except ValueError:
        return json.dumps({'status': 1, 'info': 'request failed.'})

    current_ts = time.time()
    _id = False
    d.update(timestamp=current_ts)

    perm = ts_can_insert(d.get('auth'), current_ts) and token_can_insert(d.get('auth'))

    if perm:
        _id = col.insert_one(d).inserted_id
    if _id:
        return json.dumps({'status': 0, 'info': 'success'})
    else:
        return json.dumps({'status': 2, 'info': 'op too frequent or invalid token.'})


def ts_can_insert(auth_code, current_ts):
    db_ts = 0
    for i in col.find({'auth': auth_code}).sort('timestamp', pymongo.DESCENDING):
        db_ts = i['timestamp']
        break

    return True if current_ts - db_ts >= 180 else False


# TODO: valid[] shouldn't be global since user may add server in Telegram.
# TODO: but query database every 180 seconds in two loop is a bad idea.
def token_can_insert(auth_code):
    col2 = db['user']
    valid = [j for i in col2.find() for j in i['server']]
    return True if auth_code in valid else False


if __name__ == '__main__':
    path = '/etc/letsencrypt/live/serversan.date/'
    context = (path + 'fullchain.pem', path + 'privkey.pem')
    app.run(host='api.serversan.date', ssl_context=context)
    # app.run()
