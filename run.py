import os
import re
import sys
from datetime import datetime
from getpass import getpass
from time import sleep

from oc import kill_existing_oc, get_server_cert, reconnect_oc, ensure_oc_connected, stop_oc_check
from ping import ping
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
    settings.setup(load_from_env=False)
    settings.save()


if 'setup' in sys.argv:
    setup()
    print('Setup successfully completed. you can run <python3 run.py>')
    sys.exit(0)

correct = False
load_from_env = True
while not force and not correct:
    settings.get_environments(load_from_env=load_from_env)
    print('host: {server}, username: {username}, password: ***, ping timeout: {ping_timeout}'
          .format(server=config['server'], username=config['username'], ping_timeout=config['ping_timeout']))
    i = input('Correct? (Y/n)')
    correct = not i or i.lower() == 'y'
    if not correct:
        load_from_env = False

settings.save()

if not force and not settings.login_pass:
    settings.login_pass = getpass('System password: ')

kill_existing_oc()
get_server_cert()
reconnect_oc(force)

# try more times on first connection to let establish
# the connection, then check connectivity
more_try_times = 10
try_times = 3

down_count = -more_try_times
down_ping_count = -more_try_times

ping_timeout = int(config.get('ping_timeout', settings.DEFAULT_PING_TIMEOUT))

while True:
    is_up = True

    ttl, time = ping(ping_address, ping_timeout)
    print(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ttl: {ttl}, time: {time}')
    if time < 0 or time > ping_timeout:
        down_count += 1
        print('tried {down_count} times'.format(down_count=down_count))
        if down_count >= try_times:
            down_count = 0
            is_up = False
    else:
        down_count = down_ping_count = 0

    if is_up:
        if not ensure_oc_connected():
            down_count = 999

    if is_up:
        print(ping_address, 'is up!')
    else:
        down_count = down_ping_count = -more_try_times
        stop_oc_check()
        if force:
            break
        reconnect_oc(force)
        print(ping_address, 'is down!')

    sleep(1)
