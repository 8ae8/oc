import re
import sys
from datetime import datetime
from getpass import getpass
from time import sleep

from log import Log
from oc import oc_client
from ping import ping
from settings import settings

settings.load()
oc_client.kill_existing_oc()
ping_address = settings.g.get('ping_address', '8.8.8.8')

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

correct = False
do_load_from_env = True
force_list_profile = False
selected_number = None


def proc():
    global is_adding, do_load_from_env, force_list_profile, selected_number

    q = 'Which one?'
    if selected_number:
        q += f' ({selected_number}) '
    _i = input(q)
    if not is_adding:
        if not _i:
            _i = selected_number
        try:
            if _i:
                selected_number = int(_i)
                return True
        except:
            return None
    if _i:
        _i = _i.lower()
        if _i == 'a':
            is_adding = True
            do_load_from_env = False
            return None
        else:
            d = re.findall('d (\d+)', _i)
            if d:
                ind = int(d[0])
                ind -= 1
                if 0 <= ind < len(settings.profiles):
                    del settings.profiles[ind]
                    force_list_profile = True
                    do_load_from_env = True
                    settings.current_profile.clear()
                return None
            else:
                print('You must pass item number to delete profile (e.g. d 1).')
                return proc()


while not settings.is_background and not correct:
    settings.get_environments(load_from_env=do_load_from_env)
    settings.save()
    is_adding = False
    print(f'ping timeout: {settings.g["ping_timeout"]}')
    if len(settings.profiles) > 0:
        if force_list_profile or len(settings.profiles) > 1:
            selected_number = None
            print()
            print('[option] [arg]')
            print('Options:')
            print('a\t: add new profile')
            print('d\t: delete existing profile(d {index})')
            print()
            print('profiles:')
            print('- Enter profile number/option which is described:')
            print()
            selected_profile = settings.g.get('selected_profile', -1)
            for i, conf in enumerate(settings.profiles):
                if selected_profile == i + 1:
                    selected_number = i + 1
                    selected_char = '*'
                else:
                    selected_char = ' '
                print(f'{selected_char} {i + 1}- host: {conf["server"]}, '
                      f'username: {conf["username"]}, password: ***')
            print()

            if not proc():
                continue
        else:
            selected_number = 1
        settings.select_config(selected_number - 1)

        if not is_adding:
            print(f'Selected {selected_number}- host: {settings.current_profile["server"]}, '
                  f'username: {settings.current_profile["username"]}, password: ***')
            i = input('Correct? (Y/n) ')
            correct = not i or i.lower() == 'y'
        if not correct:
            do_load_from_env = False

settings.save()

Log.initialize(settings.is_background)

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

ping_timeout = int(settings.current_profile.get('ping_timeout', settings.DEFAULT_PING_TIMEOUT))

while True:
    is_up = True
    ttl, time = ping(ping_address, ping_timeout)
    Log.debug(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ttl: {ttl}, time: {time}')
    if time < 0 or time > ping_timeout:
        down_count += 1
        Log.debug('tried {down_count} times'.format(down_count=down_count))
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
        Log.debug(f'{ping_address} is up!')
    else:
        down_count = down_ping_count = -more_try_times
        oc_client.check_process_enabled = False
        if settings.is_background:
            sys.exit()
        oc_client.reconnect_oc()
        Log.debug(f'{ping_address} is down!')

    sleep(1)
