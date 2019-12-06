import os
import re
import sys
import subprocess
from threading import Thread

from time import sleep
from uuid import uuid4

import errno

from log import Log
from settings import settings

pid_file_path = 'oc.pid'


class ClientHandler:
    def __init__(self):
        self.key = None
        self.disconnect_patterns = [
            'reconnecting'
        ]
        self._is_process_running = True
        self._is_connected = False
        self._check_process_enabled = True

    @property
    def is_connected(self):
        return self._is_connected and self.is_process_running

    @is_connected.setter
    def is_connected(self, value):
        self._is_connected = value

    @property
    def is_process_running(self):
        return self._is_process_running

    @is_process_running.setter
    def is_process_running(self, value):
        self._is_process_running = value

    @property
    def check_process_enabled(self):
        return self._check_process_enabled

    @check_process_enabled.setter
    def check_process_enabled(self, value):
        self._check_process_enabled = value

    @staticmethod
    def get_server_cert():
        result = subprocess.getoutput(f"echo {settings.current_profile['password']} | openconnect "
                                      f"--no-dtls --authgroup MGT {settings.current_profile['server']}"
                                      f" --passwd-on-stdin")
        cert = re.findall('--servercert (.+)\n', result)
        if not cert:
            Log.error('could not read server cert')
            sys.exit()
        cert = cert[0]
        settings.server_cert = cert
        Log.info('server cert: {cert}'.format(cert=cert))

    def kill_existing_oc(self):
        try:
            pids = list()
            if os.path.exists(pid_file_path):
                with open(pid_file_path, 'r') as file:
                    pid = file.read().replace('\n', '')
                    pids.append(str(pid))
                os.remove(pid_file_path)
            if settings.current_pid:
                pids.append(str(settings.current_pid))
            if pids:
                os.system(f"echo {settings.login_pass}|sudo -S kill -9 {' '.join(pids)}")
        except:
            pass
        self.is_process_running = False

    def reconnect_oc(self):
        self.kill_existing_oc()
        Log.info('connecting oc...')
        if not self.key:
            self.key = uuid4().hex
        if settings.is_background:
            cmd = f'echo {settings.current_profile["password"]} | openconnect ' \
                  f'-u {settings.current_profile["username"]} --authgroup MGT ' \
                  f'--servercert {settings.server_cert} {settings.current_profile["server"]} ' \
                  f'--passwd-on-stdin --background --pid-file {pid_file_path} ' \
                  f'--useragent={self.key}'
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            settings_path = os.path.join(current_dir, 'settings.json')
            cmd = f'echo {settings.login_pass}|sudo -S python3 {os.path.join(current_dir, "run.py")} ' \
                  f'-b -s {settings_path} -k {self.key}'
        self.is_process_running = True
        self.is_connected = True
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        settings.current_pid = process.pid
        Thread(target=self.check_process_running, args=(process,)).start()
        Thread(target=self.read_process_output, args=(process,)).start()

    def pid_exists(self, pid):
        if pid <= 0:
            self.is_process_running = False
            return False
        try:
            os.kill(pid, 0)
        except OSError as err:
            if err.errno == errno.ESRCH:
                # ESRCH == No such process
                self.is_process_running = False
            elif err.errno == errno.EPERM:
                # access denied
                self.is_process_running = True
            else:
                # According to "man 2 kill" possible error values are
                # (EINVAL, EPERM, ESRCH)
                raise
        else:
            self.is_process_running = True
        return self.is_process_running

    def check_process_running(self, process):
        self.check_process_enabled = True
        if process:
            while True:
                if not self.check_process_enabled:
                    return
                sleep(1)
                exists = False
                if not settings.is_background:
                    if self.pid_exists(settings.current_pid):
                        exists = True
                else:
                    if not self.key:
                        Log.debug('waiting for process to run')
                        continue
                    out, _ = subprocess.Popen(f'ps a | grep {self.key}', shell=True,
                                              stdout=subprocess.PIPE).communicate()
                    if out:
                        key = 'openconnect'
                        items = out.decode().split('\n')
                        for item in items:
                            if not item:
                                continue
                            if key in item:
                                exists = True
                                break
                self.is_process_running = exists

    def read_process_output(self, process):
        self.check_process_enabled = True
        if process:
            while True:
                if not self.check_process_enabled:
                    return
                sleep(1)
                output = process.stdout.readline()
                poll = process.poll()
                if not output and (not poll or poll < 0):
                    # Log.debug('oc Disconnected with no output!')
                    self.is_connected = False
                    sleep(10)
                    continue

                if output:
                    output = output.decode().strip()
                    # Log.debug(f'> output: {output}')
                    for item in self.disconnect_patterns:
                        if item in output:
                            Log.debug('> oc Disconnected!')
                            self.is_connected = False


oc_client = ClientHandler()
