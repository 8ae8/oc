import os
import re
import sys
import subprocess
from threading import Thread

from settings import settings, config

pid_file_path = 'oc.pid'


def get_server_cert():
    result = subprocess.getoutput("echo '-' | openconnect --authgroup MGT {server} --passwd-on-stdin"
                                  .format(server=config['server']))
    cert = re.findall('--servercert (.+)\n', result)
    if not cert:
        print('could not read server cert')
        sys.exit()
    cert = cert[0]
    settings.server_cert = cert
    print('server cert: {cert}'.format(cert=cert))


def kill_existing_oc():
    global is_connected
    try:
        pids = list()
        with open(pid_file_path, 'r') as file:
            pid = file.read().replace('\n', '')
            pids.append(str(pid))
        if settings.current_pid:
            pids.append(str(settings.current_pid))
        if pids:
            os.system("echo {login_pass}|sudo -S kill -9 {pids}"
                      .format(login_pass=settings.login_pass, pids=' '.join(pids)))
    except:
        pass
    is_connected = False


def reconnect_oc(force):
    global is_connected
    kill_existing_oc()
    print('connecting oc...')
    if not force:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        settings_path = os.path.join(current_dir, 'settings.json')
        cmd = 'echo {login_pass}|sudo -S python3 {current_path} -f -s {settings_path}' \
            .format(login_pass=settings.login_pass, current_path=os.path.join(current_dir, 'run.py'),
                    settings_path=settings_path)
    else:
        cmd = "echo '{password}' | openconnect -u {username} --authgroup MGT --servercert {cert} {server} " \
                 "--passwd-on-stdin --background --pid-file {pid_file_path}" \
            .format(password=config['password'], username=config['username'], cert=settings.server_cert,
                    server=config['server'], pid_file_path=pid_file_path)
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    t = Thread(target=read_process_output, args=(process,))
    t.start()
    settings.current_pid = process.pid
    is_connected = True


is_connected = False
disconnect_patterns = [
    'reconnecting'
]


def read_process_output(process):
    global is_connected
    if process:
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break

            if output:
                output = output.decode().strip()
                print('> ' + output)
                for item in disconnect_patterns:
                    if item in output:
                        print('> oc Disconnected!')
                        is_connected = False
                        break
        rc = process.poll()
        return rc


def ensure_oc_connected():
    return is_connected
