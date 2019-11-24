import logging
import sys
from datetime import datetime
from getpass import getpass
from time import sleep

import os

from oc import oc_client
from ping import ping
from settings import settings, config

settings.load()
oc_client.kill_existing_oc()
ping_address = config.get('ping_address', '8.8.8.8')

current_pid = None
get_from_env = True

settings.is_background = '-b' in sys.argv
if '-s' in sys.argv:
    si = sys.argv.index('-s')
    if si:
        settings.file_path = sys.argv[si + 1]

if '-k' in sys.argv:
    ki = sys.argv.index('-k')
    if ki:
        oc_client.key = sys.argv[ki + 1]


def setup():
    settings.setup(load_from_env=False)
    settings.save()


if 'setup' in sys.argv:
    setup()
    print('Setup successfully completed. you can run <python3 run.py>')
    sys.exit(0)

# log
log_enabled = '-l' in sys.argv
log_path = 'oc.log'
if settings.is_background:
    if os.path.exists(log_path):
        os.remove(log_path)
log_kwargs = dict()
if log_enabled:
    log_kwargs.update(dict(filename=log_path, filemode='a'))
logging.basicConfig(
    **log_kwargs,
    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
    level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
#

correct = False
load_from_env = True
while not settings.is_background and not correct:
    settings.get_environments(load_from_env=load_from_env)
    print('host: {server}, username: {username}, password: ***, ping timeout: {ping_timeout}'
          .format(server=config['server'], username=config['username'], ping_timeout=config['ping_timeout']))
    i = input('Correct? (Y/n)')
    correct = not i or i.lower() == 'y'
    if not correct:
        load_from_env = False

settings.save()

if not settings.is_background and not settings.login_pass:
    settings.login_pass = getpass('System password: ')

oc_client.kill_existing_oc()
oc_client.get_server_cert()
oc_client.reconnect_oc()

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
    logging.debug(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ttl: {ttl}, time: {time}')
    if time < 0 or time > ping_timeout:
        down_count += 1
        logging.debug('tried {down_count} times'.format(down_count=down_count))
        if down_count >= try_times:
            down_count = 0
            is_up = False
    else:
        down_count = down_ping_count = 0

    if is_up:
        is_up = oc_client.is_process_running
        if not oc_client.is_connected:
            down_count = 999

    if is_up:
        logging.debug(f'{ping_address} is up!')
    else:
        down_count = down_ping_count = -more_try_times
        oc_client.check_process_enabled = False
        if settings.is_background:
            sys.exit()
        oc_client.reconnect_oc()
        logging.debug(f'{ping_address} is down!')

    sleep(1)
