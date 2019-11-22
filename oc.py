import os
import re
import sys
import subprocess
from threading import Thread

import errno
from time import sleep

from settings import settings, config

pid_file_path = 'oc.pid'


class ClientHandler:
    _is_connected = False
    _check_process = True
    process_running = True
    disconnect_patterns = [
        'reconnecting'
    ]

    @property
    def is_connected(self):
        self.process_running = True
        return self._is_connected and self.process_running

    @is_connected.setter
    def is_connected(self, value):
        self._is_connected = value

    @property
    def check_process(self):
        return self._check_process

    @check_process.setter
    def check_process(self, value):
        self._check_process = value

    @staticmethod
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

    def kill_existing_oc(self):
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
        self.is_connected = False

    def reconnect_oc(self, force):
        self.kill_existing_oc()
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
        settings.current_pid = process.pid
        self.is_connected = True
        # if force:
        t = Thread(target=self.read_process_output, args=(process,))
        t.start()

    def pid_exists(self, pid):
        if pid <= 0:
            self.process_running = False
            return False
        try:
            os.kill(pid, 0)
        except OSError as err:
            if err.errno == errno.ESRCH:
                # ESRCH == No such process
                self.process_running = False
            elif err.errno == errno.EPERM:
                print(f"access to PID {pid} denied")
                self.process_running = True
            else:
                # According to "man 2 kill" possible error values are
                # (EINVAL, EPERM, ESRCH)
                raise
        else:
            self.process_running = True
        return self.process_running

    def read_process_output(self, process):
        self.check_process = True
        if process:
            while True:
                if not self.check_process:
                    print('process output check stopped')
                    return
                sleep(1)
                with open('oc.pid') as f:
                    pid = int(f.readline().strip())
                if not self.pid_exists(pid):
                    print(f"process PID {pid} does not exist")
                    self.process_running = False
                output = process.stdout.readline()
                poll = process.poll()
                if not output and (not poll or poll < 0):
                    print('oc Disconnected with no output!')
                    self.is_connected = False
                    sleep(10)
                    continue

                if output:
                    output = output.decode().strip()
                    print(f'> output: {output}')
                    for item in self.disconnect_patterns:
                        if item in output:
                            print('> oc Disconnected!')
                            self.is_connected = False
            print('oc process check Done!')


oc_client = ClientHandler()
