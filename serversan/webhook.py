#!/usr/bin/python
# coding:utf-8

# ServerSan - webhook.py
# 2018/3/15 11:08
#

__author__ = 'Benny <benny@bennythink.com>'
import json
import os
# TODO: or MongoDB, maybe.
import pymysql
from flask import Flask, request

from config import username, password

un = os.environ.get('user') or username
pwd = os.environ.get('password') or password

con = pymysql.connect(host='127.0.0.1', user=un, password=pwd)

# cur = con.cursor()
# cur.execute('show databases')

app = Flask(__name__)


@app.route("/v1/create", methods=['POST'])
def hello():
    try:
        d = json.loads(request.data)
    except ValueError:
        return json.dumps({'status': 1, 'info': 'request failed.'})

    # database
    print d.get('auth')

    return json.dumps({'status': 0, 'info': 'success'})


if __name__ == '__main__':
    app.run()
