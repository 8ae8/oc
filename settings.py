import json
import os
from getpass import getpass


class Settings:
    DEFAULT_SERVER_KEY = 'oc_server'
    DEFAULT_USERNAME_KEY = 'oc_username'
    DEFAULT_PASSWORD_KEY = 'oc_password'
    DEFAULT_PING_TIMEOUT = '2000'

    file_path = 'settings.json'
    login_pass = None
    current_pid = None
    server_cert = None

    def __init__(self):
        self.config = dict()

    def load(self):
        self.config['ping_timeout'] = self.DEFAULT_PING_TIMEOUT
        if not os.path.exists(self.file_path):
            return
        with open(self.file_path, 'r') as f:
            content = f.read()
            self.config.update(json.loads(content))

    def save(self):
        with open(self.file_path, 'w+') as f:
            f.write(json.dumps(self.config))

    def get_env(self, key, message, default=None, is_password=False, load_from_env=True):
        env = None
        if load_from_env:
            env = os.environ.get(key) if load_from_env else None
            if not env:
                env = self.config.get(key)
        if not env:
            if default:
                message += f' ({default})'
            env = (getpass if is_password else input)(message + ': ')
            if not env:
                env = default
            self.config[key] = env
        return env

    def get_environments(self, load_from_env=True):
        self.config['server'] = self.get_env(self.config.get('server_key', self.DEFAULT_SERVER_KEY),
                                             'Server (IP/URL:Port)', load_from_env=load_from_env)
        self.config['username'] = self.get_env(self.config.get('username_key', self.DEFAULT_USERNAME_KEY),
                                               'Username', load_from_env=load_from_env)
        self.config['password'] = self.get_env(self.config.get('password_key', self.DEFAULT_PASSWORD_KEY),
                                               'Password', is_password=True, load_from_env=load_from_env)

    def setup(self, load_from_env=True):
        self.config['server_key'] = self.get_env('server_key', 'Key of server in environment',
                                                 default=self.DEFAULT_SERVER_KEY, load_from_env=load_from_env)
        self.config['username_key'] = self.get_env('username_key', 'Key of username in environment',
                                                   default=self.DEFAULT_USERNAME_KEY, load_from_env=load_from_env)
        self.config['password_key'] = self.get_env('password_key', 'Key of password in environment',
                                                   default=self.DEFAULT_PASSWORD_KEY, load_from_env=load_from_env)
        self.config['ping_timeout'] = self.get_env('ping_timeout', 'Maximum ping timeout in milliseconds',
                                                   default=settings.DEFAULT_PING_TIMEOUT, load_from_env=load_from_env)


settings = Settings()
config = settings.config
