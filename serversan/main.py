#!/usr/bin/python
# coding:utf-8

# ServerSan - main.py
# 2018/3/15 13:43
# 

__author__ = 'Benny <benny@bennythink.com>'

import os
import sys
import time
from base64 import b64encode

import pymongo
import telebot
from telebot import types
from apscheduler.schedulers.background import BackgroundScheduler

bot = telebot.TeleBot(sys.argv[1])
client = pymongo.MongoClient()
db = client['ServerSan']
user_col = db['user']
sysinfo_col = db['sysinfo']
log_col = db['loginfo']


@bot.message_handler(commands=['start'])
def bot_start(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id, u'Welcome %s!😗\n'
                                      'ServerSan is a server status monitor Telegram Bot. '
                                      'This bot is under actively development, '
                                      'and *DOES NOT* provide any reliability for now.\n'
                                      'Please click /help for support.' % message.chat.first_name,
                     parse_mode='Markdown')


@bot.message_handler(commands=['help'])
def bot_help(message):
    bot.send_chat_action(message.chat.id, 'typing')
    bot.send_message(message.chat.id,
                     "Developer @BennyThink \n"
                     "GitHub https://github.com/BennyThink/ExpressBot \n"
                     "Feel free to open an issue or talk to me directly!")


@bot.message_handler(commands=['add'])
def add_server(message):
    server_token = generate_token()
    if message.chat.last_name is None:
        message.chat.last_name = ''

    user_info = user_col.find_one({'userID': message.chat.id})
    if user_info is None:
        user_info = dict(userID=message.chat.id, username=message.chat.username,
                         nickname=message.chat.first_name + message.chat.last_name,
                         role=1000, server=[server_token], notify=1)
    else:
        server_block = user_info['server']
        server_block.append(server_token)
        user_info.update(server=server_block)

    if user_col.update_one({'userID': message.chat.id}, {'$set': user_info}, upsert=True).acknowledged:
        bot.send_chat_action(message.chat.id, 'typing')
        bot.send_message(message.chat.id,
                         "Execute the following command(unused server will be deleted within 30 minutes):\n\n"
                         "`wget https://raw.githubusercontent.com/BennyThink/ServerSan/master/install.sh"
                         "&& bash install.sh %s`" % server_token, parse_mode='Markdown')
    else:
        bot.send_chat_action(message.chat.id, 'typing')
        bot.send_message(message.chat.id, 'Something is going wrong')


def generate_token():
    return b64encode(os.urandom(16))


@bot.message_handler(commands=['stat'])
def stat(message):
    markup = create_server_markup(message.chat.id, 'stat')
    if markup.to_dic()['inline_keyboard']:
        bot.send_message(message.chat.id, 'Which server do you want to view?', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Oww you don\'t have any servers, click /add to add one.')


@bot.message_handler(commands=['del'])
def delete(message):
    markup = create_server_markup(message.chat.id, 'delete')
    if markup.to_dic()['inline_keyboard']:
        bot.send_message(message.chat.id, 'Which server do you want to delete?', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Oww you don\'t have any servers.')


def create_server_markup(chat_id, op):
    one_latest_server = get_user_server(chat_id)

    btn_list = []
    count = len(one_latest_server)
    size = 2
    markup = types.InlineKeyboardMarkup(size)
    for index in range(0, count):
        btn_list.append(types.InlineKeyboardButton(
            "%s %s" % (one_latest_server[index]['hostname'], one_latest_server[index]['ip']),
            callback_data='%s %s' % (op, index)))

    for i in range(0, len(btn_list), size):
        part = btn_list[i:i + size]
        if len(part) == 3:
            markup.add(part[0], part[1], part[2])
        elif len(part) == 2:
            markup.add(part[0], part[1])
        else:
            markup.add(part[0])

    return markup


@bot.callback_query_handler(func=lambda call: True)
def callback_handle(call):
    if 'stat' in call.data:
        info, notify = parse_data(get_user_server(call.message.chat.id)[int(call.data.split()[1])])
        bot.answer_callback_query(call.id, 'Your info for %s' % notify)
        bot.send_message(call.message.chat.id, info, parse_mode='HTML')
    elif 'delete' in call.data:
        # delete is two step, delete server block and systat
        info = get_user_server(call.message.chat.id)[int(call.data.split()[1])]
        user_id = call.message.chat.id
        auth_code = info['auth']

        bot.answer_callback_query(call.id, 'Deleting your server %s' % info['hostname'])
        msg = 'Your server has been deleted.' if delete_server(user_id, auth_code) else 'Something\'s wrong'
        markup = create_server_markup(user_id, 'delete')
        bot.edit_message_reply_markup(user_id, call.message.message_id, reply_markup=markup)
        bot.send_message(call.message.chat.id, msg)


def delete_server(_id, auth_code):
    server_block = user_col.find_one({'userID': _id})['server']
    server_block.pop(server_block.index(auth_code))

    r1 = sysinfo_col.delete_many({'auth': auth_code}).acknowledged
    r2 = user_col.update_one({'userID': _id}, {"$set": {'server': server_block}}).acknowledged

    if r1 and r2:
        return True


def parse_data(latest_info):
    """
    parse dict to string.
    :param latest_info: the latest info about one server
    :return: string to be sent
    """
    return u'''Your server <code>%s</code> on %s info:\n
    System Uptime: %s
    OS: %s
    Kernel: %s
    Process: %s
    Sessions: <code>%s</code>
    CPU Model: %s
    CPU Speed: %sx %s GHz
    Network Activity↑↓:%s KiB/s %s KiB/s
    CPU utilization: <b>%s</b> %%
    RAM: %s MiB of %s MiB , <b>%s%%</b>
    SWAP: %s MiB of %s MiB , <b>%s%%</b>
    Disk: %s GiB of %s GiB, <b>%s%%</b>
    Top Process: \n%s''' % (latest_info['hostname'], latest_info['ip'],
                            parse_uptime(latest_info['uptime']),
                            latest_info['os'][0],
                            latest_info['os'][1],
                            latest_info['pro'],
                            latest_info['session'],
                            latest_info['cpu'][0],
                            latest_info['cpu'][1], latest_info['cpu'][2],
                            latest_info['network'][0], latest_info['network'][1],

                            latest_info['percent'],
                            latest_info['mem'][0], latest_info['mem'][1], latest_info['mem'][2],
                            latest_info['swap'][0], latest_info['swap'][1], latest_info['swap'][2],
                            latest_info['disk'][0], latest_info['disk'][1], latest_info['disk'][2],
                            latest_info['top']), latest_info['hostname']


def get_server_count(_id):
    for i in user_col.find({'userID': _id}):
        return len(i.get('server'))


def server_group(auth_code):
    group = []
    for i in sysinfo_col.find({'auth': auth_code}):
        group.append(i)
    return group


def get_user_server(_id):
    """
    get designated user's all latest server 
    :param _id: user_id
    :return: [{},{}] for the newest information on one server
    """
    user_server = []
    info = 'No information'
    all_server = []

    for i in user_col.find({'userID': _id}):
        for t in i.get('server'):
            user_server.append(t)
    for token in user_server:
        for info in sysinfo_col.find({'auth': token}):
            pass
        all_server.append(info)

    return all_server


def parse_uptime(boot_time):
    p1 = time.strftime("%Y-%m-%d %H:%M", time.localtime(boot_time)) + ' up, '
    uptime = time.time() - boot_time

    day = uptime // 3600 // 24
    hour = uptime - day * 3600 * 24
    minute = hour - hour // 3600 * 3600
    return p1 + '%d days %d:%d' % (day, hour // 3600, minute // 60)


def del_unused_server():
    blocks = [(j, i['userID']) for i in user_col.find() for j in i['server']]

    for i in blocks:
        if sysinfo_col.find_one({'auth': i[0]}) is None:
            delete_server(i[1], i[0])


def resource_warning():
    auth_list = list(set([i['auth'] for i in sysinfo_col.find()]))
    data = None
    latest_each = []

    for i in auth_list:
        for j in sysinfo_col.find({'auth': i}):
            data = j
        latest_each.append(data)

    for each in latest_each:
        if time.time() - each['timestamp'] > 900:
            warning_send(u'⚠Warning⚠\nYour server %s has lost connection for 900 seconds' % each['hostname'],
                         each['auth'])
        elif each['percent'] > 90.0 or each['mem'][2] > 90.0 or each['swap'][2] > 60.0:
            warning_send(u'''⚠Warning⚠\nYour server %s is consuming a lot of resources.
            CPU utilization: %s %%
            Ram usage: %s %%
            Swap usage: %s %%
            Disk usage: %s %%
            -------------------
            Top process:\n%s''' % (
                each['hostname'], each['percent'], each['mem'][2], each['swap'][2], each['disk'][2], each['top']),
                         each['auth'])

        elif each['disk'][2] > 80.0:
            warning_send(u'''⚠Warning⚠\nYour server %s is not having enough free disk space.
            Current disk status is showing as follows:
            Used: %s GiB
            All: %s GiB
            Percentage: %s %%''' % (
                each['hostname'], each['disk'][0], each['disk'][1], each['disk'][2]), each['auth'])


def warning_send(msg, auth):
    last_sent = log_col.find_one({'auth': auth})['timestamp']
    for i in user_col.find():
        if auth in i['server'] and i['notify'] and (time.time() - last_sent) > 14400:
            bot.send_message(i['userID'], msg)
            log_col.update_one({'auth': auth}, {'$set': {'timestamp': time.time()}}, upsert=True)


def del_old_records(sec):
    for i in sysinfo_col.find():
        if time.time() - i['timestamp'] > sec:
            sysinfo_col.delete_one({'timestamp': i['timestamp']})


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(del_unused_server, 'interval', minutes=30)
    scheduler.add_job(resource_warning, 'interval', minutes=10)
    # scheduler.add_job(del_old_records, 'cron', day='*/180', args=[180 * 24 * 3600])
    scheduler.start()
    bot.polling(none_stop=True)
