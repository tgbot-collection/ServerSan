#!/usr/bin/python
# coding:utf-8

# ServerSan - ss-agent.py
# 2018/3/14 15:03
# 

__author__ = 'Benny <benny@bennythink.com>'
__version__ = '0.0.1'

import os
import platform
import socket
import time

import cpuinfo
import psutil
import requests

API = 'http://127.0.0.1:5000/'


def get_uptime():
    return psutil.boot_time()


def get_os():
    if platform.system() == 'Windows':
        uname = platform.uname()
        return '%s %s %s' % (uname[0], uname[2], uname[4])
    else:
        uname = platform.dist()
        return '%s %s %s %s' % (uname[0], uname[1], uname[2], platform.machine())


def get_kernel():
    info = platform.version() if platform.system() == 'Windows' else platform.release()
    return info


def get_process_count():
    return len(psutil.pids())


def get_sessions():
    info = '%d user(s) in Total' % len(psutil.users())
    for user in psutil.users():
        info += '\n%s on %s from %s at %s' % (
            user[0], user[1], user[2], time.strftime("%Y-%m-%d %H:%M", time.localtime(user[3])))
    return info


def get_cpu_model():
    return cpuinfo.get_cpu_info()['brand']


def get_cpu_count():
    return psutil.cpu_count()


def get_cpu_freq():
    # return '%d x %s MHz' % (psutil.cpu_count(), psutil.cpu_freq()[0])
    return psutil.cpu_freq()[0]


def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def network_activity():
    old_value = old_value2 = 0
    while True:
        new_value = psutil.net_io_counters().bytes_recv
        new_value2 = psutil.net_io_counters().bytes_sent

        if old_value:
            rx = (new_value - old_value) / 1024.0
            tx = (new_value2 - old_value2) / 1024.0
            rx_tx = (new_value - old_value + new_value2 - old_value2) / 1024.0
            break
        old_value = new_value
        old_value2 = new_value2
        time.sleep(1)
    return [tx, rx, rx_tx]


def current_network_flow():
    rx = round(psutil.net_io_counters().bytes_recv / 1024.0 / 1024 / 1024, 2)
    tx = round(psutil.net_io_counters().bytes_sent / 1024.0 / 1024 / 1024, 2)
    return [rx, tx]


def average_load():
    return psutil.cpu_percent()


def mem():
    used = round(psutil.virtual_memory().used / 1024.0 / 1024, 2)
    total = round(psutil.virtual_memory().total / 1024.0 / 1024, 2)
    percent = psutil.virtual_memory().percent
    return [used, total, percent]


def swap():
    used = round(psutil.swap_memory().used / 1024.0 / 1024, 2)
    total = round(psutil.swap_memory().total / 1024.0 / 1024, 2)
    percent = psutil.swap_memory().percent
    return [used, total, percent]


def disk():
    used = round(psutil.disk_usage('/').used / 1024.0 / 1024 / 1024, 2)
    total = round(psutil.disk_usage('/').total / 1024.0 / 1024 / 1024, 2)
    percent = psutil.disk_usage('/').percent
    return [used, total, percent]


# def top_process():
#     process_list = []
#     for pid in psutil.process_iter():
#         pid.cpu_percent()
#     time.sleep(1)
#     for pid in psutil.process_iter():
#         process_list.append((pid.cpu_percent(), pid.pid, pid.name(), round(pid.memory_info().vms / 1024.0 / 1024, 2)))
#
#     for i in range(len(process_list) - 1):
#         if process_list[i][0] < process_list[i + 1][0]:
#             process_list[i], process_list[i + 1] = process_list[i + 1], process_list[i]
#     return process_list[0:4]

def top_process():
    cmd = 'ps axc -o uname:12,pcpu,rss,cmd --sort=-pcpu,-rss --noheaders --width 120|head'
    with os.popen(cmd) as p:
        pro = p.read()
    info = pro if pro else 'Windows is not supported.'
    return info


def build():
    message = dict(auth=get_auth_token(), uptime=get_uptime(), os=[get_os(), get_kernel()],
                   pro_count=get_process_count(),
                   session=get_sessions(), cpu=[get_cpu_model(), get_cpu_count(), get_cpu_freq()],
                   ip=get_host_ip(), network=network_activity(), flow=current_network_flow(),
                   load=average_load(), mem=mem(), swap=swap(), disk=disk(), top=top_process()
                   )
    return message


def send_request(dic):
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    print(requests.post(API + 'v1/create', json=dic, headers=headers).status_code)


def get_auth_token():
    path = os.environ.get('HOMEPATH') + '/ss-auth.log' if platform.system() == 'Windows' \
        else '/etc/serversan/ss-auth.log'

    with open(path) as f:
        return f.read()


# TODO: upgrade client agent: shell scripts or ...?
def upgrade():
    pass


def main():
    json_result = build()
    send_request(json_result)


if __name__ == '__main__':
    main()
