import json
import os, re
import subprocess
from getpass import getpass
from time import sleep
from datetime import datetime

import sys

settings_path = 'settings.json'
settings = {}


def load_settings():
    global settings
    if not os.path.exists(settings_path):
        return
    with open(settings_path, 'r') as f:
        settings = f.read()
        settings = json.loads(settings)
    return settings


load_settings()
login_pass = None
ping_address = settings.get('ping_address', '8.8.8.8')
pid_file_path = 'oc.pid'
current_pid = None

get_from_env = True


def save_settings():
    global settings
    with open(settings_path, 'w+') as f:
        f.write(json.dumps(settings))


def setup():
    settings['server_key'] = input('Key of server in environment: ')
    settings['username_key'] = input('Key of username in environment: ')
    settings['password_key'] = input('Key of password in environment: ')
    save_settings()


if 'setup' in sys.argv:
    setup()

force_run = '-f' in sys.argv
if '-s' in sys.argv:
    si = sys.argv.index('-s')
    if si:
        settings_path = sys.argv[si + 1]


def get_env(key, message, is_password=False):
    global settings, get_from_env
    env = None
    if get_from_env:
        env = os.environ.get(key) if get_from_env else None
        if not env:
            print('environment with key `%s` not found, trying to load from settings' % key)
            env = settings.get(key)
    if not env:
        env = (getpass if is_password else input)(message)
        settings[key] = env
    return env


server, username, password = None, None, None


def get_environments():
    global server, username, password
    server = get_env('oc_server', 'Server (IP/URL:Port): ')
    username = get_env('oc_username', 'Username: ')
    password = get_env('oc_password', 'Password: ')


get_environments()
if server and username and password:
    if not force_run:
        print('host: {server}, username: {username}, password: ***'
              .format(server=server, username=username))
        correct = input('Correct? (Y/n)')
        if correct and correct.lower() != 'y':
            get_from_env = False
            get_environments()
else:
    print('Not enough data')
    sys.exit()

save_settings()


def kill_existing_oc():
    try:
        pids = list()
        with open(pid_file_path, 'r') as file:
            pid = file.read().replace('\n', '')
            pids.append(str(pid))
        if current_pid:
            pids.append(str(current_pid))
        if pids:
            os.system("echo {login_pass}|sudo -S kill -9 {pids}".format(login_pass=login_pass, pids=' '.join(pids)))
    except:
        pass


def reconnect_oc():
    global server, username, password, settings_path, get_from_env, current_pid

    print('reconnecting oc...')

    kill_existing_oc()

    if not force_run:
        current_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_path)
        settings_path = os.path.join(current_dir, 'settings.json')
        cmd = 'echo {login_pass}|sudo -S python3 {current_path} -f -s {settings_path}' \
            .format(login_pass=login_pass, current_path=current_path, settings_path=settings_path)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        current_pid = p.pid
        return
    oc_cmd = "echo '{password}' | openconnect -u {username} --authgroup MGT --servercert {cert} {server} " \
             "--passwd-on-stdin --background --pid-file {pid_file_path}" \
        .format(password=password, username=username, cert=cert, server=server, pid_file_path=pid_file_path)
    os.system(oc_cmd)


if not force_run:
    if not login_pass:
        login_pass = getpass('Password: ')

kill_existing_oc()

result = subprocess.getoutput("echo '-' | openconnect --authgroup MGT {server} --passwd-on-stdin"
                              .format(server=server))
cert = re.findall('--servercert (.+)\n', result)
if not cert:
    print('could not read server cert')
    sys.exit()
cert = cert[0]
print('server cert: {cert}'.format(cert=cert))

reconnect_oc()

down_count = 0
down_ping_count = 0

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

    if not first_time or 0 < first_time > 1000:
        down_count += 1
        print('tried {down_count} times'.format(down_count=down_count))
        if down_count > 3:
            down_count = 0
            is_up = False
    elif 0 < first_time < 700:
        down_count = down_ping_count = 0

    if is_up:
        print(ping_address, 'is up!')
    else:
        down_count = 0
        down_ping_count = 0
        if force_run:
            break
        reconnect_oc()
        print(ping_address, 'is down!')

    sleep(1)
