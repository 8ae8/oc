import os
import re
import sys
from datetime import datetime
from getpass import getpass
from time import sleep

from oc import kill_existing_oc, get_server_cert, reconnect_oc
from settings import settings, config

settings.load()
ping_address = config.get('ping_address', '8.8.8.8')

current_pid = None
get_from_env = True

force = '-f' in sys.argv
if '-s' in sys.argv:
    si = sys.argv.index('-s')
    if si:
        settings.file_path = sys.argv[si + 1]


def setup():
    settings.setup()
    settings.save()


if 'setup' in sys.argv:
    setup()

correct = False
load_from_env = True
while not force and not correct:
    settings.get_environments(load_from_env=load_from_env)
    print('host: {server}, username: {username}, password: ***, ping timeout: {ping_timeout}'
          .format(server=config['server'], username=config['username'], ping_timeout=config['ping_timeout']))
    i = input('Correct? (Y/n)')
    correct = not i or i.lower() == 'y'
    if correct:
        load_from_env = False

settings.save()

if not force and not settings.login_pass:
    settings.login_pass = getpass('System password: ')

kill_existing_oc()
get_server_cert()
reconnect_oc(force)

down_count = 0
down_ping_count = 0
ping_timeout = int(config.get('ping_timeout', settings.DEFAULT_PING_TIMEOUT))

while True:
    ping_start_time = datetime.utcnow()
    response = os.popen("ping -c 1 " + ping_address).read()

    is_up = True

    ping_check_duration = (datetime.utcnow() - ping_start_time).total_seconds()
    if ping_check_duration > 3:
        down_ping_count += 1
        if down_ping_count > 3:
            print('Too much time for ping check %s sec' % ping_check_duration)
            is_up = False

    ttl = re.findall('ttl=(\d+)', response)
    time = re.findall('time=(.+) ms', response)
    print('{now} ttl: {ttl}, time: {time}'
          .format(now=datetime.now(),
                  ttl=ttl[0] if ttl else -1,
                  time=time[0] if time else -1))

    first_time = None
    if time:
        first_time = float(time[0])

    if not first_time or 0 < first_time > ping_timeout:
        down_count += 1
        print('tried {down_count} times'.format(down_count=down_count))
        if down_count > 3:
            down_count = 0
            is_up = False
    elif 0 < first_time < ping_timeout:
        down_count = down_ping_count = 0

    if is_up:
        print(ping_address, 'is up!')
    else:
        down_count = 0
        down_ping_count = 0
        if force:
            break
        reconnect_oc(force)
        print(ping_address, 'is down!')

    sleep(1)
