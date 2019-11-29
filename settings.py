import json
import os
from getpass import getpass


class Settings:
    DEFAULT_SERVER_KEY = 'oc_server'
    DEFAULT_USERNAME_KEY = 'oc_username'
    DEFAULT_PASSWORD_KEY = 'oc_password'
    DEFAULT_PING_TIMEOUT = '2000'

    is_background = False
    file_path = 'settings.json'
    login_pass = None
    current_pid = None
    server_cert = None
    _current_profile = dict()

    def __init__(self):
        self.profiles = list()
        self.g = dict(profiles=self.profiles, selected_profile=0)

    @property
    def current_profile(self):
        if not self._current_profile and self.profiles:
            self._current_profile = settings.profiles[0]
        return self._current_profile

    @current_profile.setter
    def current_profile(self, value):
        self._current_profile = value

    def load(self):
        self.g['ping_timeout'] = self.DEFAULT_PING_TIMEOUT
        if not os.path.exists(self.file_path):
            return
        with open(self.file_path, 'r') as f:
            content = f.read()
            g = json.loads(content)
        if isinstance(g, dict) and 'profiles' not in g:
            # is old one
            self.g['profiles'].append(g)
        else:
            self.g.update(g)
            self.profiles = self.g['profiles']
        if self.profiles:
            self.select_config(self.g['selected_profile'] - 1)

    def save(self):
        with open(self.file_path, 'w+') as f:
            f.write(json.dumps(self.g))

    def select_config(self, ind):
        if ind >= len(self.profiles):
            return None
        self.current_profile = self.profiles[ind]
        self.g['selected_profile'] = ind + 1
        return self.current_profile

    def get_env(self, key, message, static_key=None, default=None, is_password=False, load_from_env=True):
        if not static_key:
            static_key = key
        env = None
        if load_from_env:
            env = os.environ.get(key)
            if not env:
                env = self.current_profile.get(static_key)
        if not env:
            if default:
                message += f' ({default})'
            env = (getpass if is_password else input)(message + ': ')
            if not env:
                env = default
            self.current_profile[static_key] = env
        return env

    def get_environments(self, load_from_env=True):
        profile = dict()
        profile['server'] = self.get_env(self.g.get('server_key', self.DEFAULT_SERVER_KEY),
                                      'Server (IP/URL:Port)', static_key='server',
                                      load_from_env=load_from_env)
        profile['username'] = self.get_env(self.g.get('username_key', self.DEFAULT_USERNAME_KEY),
                                        'Username', static_key='username',
                                        load_from_env=load_from_env)
        profile['password'] = self.get_env(self.g.get('password_key', self.DEFAULT_PASSWORD_KEY),
                                        'Password', static_key='password', is_password=True,
                                        load_from_env=load_from_env)
        if profile not in self.profiles:
            self.profiles.append(profile)
        self.current_profile = profile

    def setup(self, load_from_env=True):
        self.g['server_key'] = self.get_env('server_key', 'Key of server in environment',
                                            default=self.DEFAULT_SERVER_KEY, load_from_env=load_from_env)
        self.g['username_key'] = self.get_env('username_key', 'Key of username in environment',
                                              default=self.DEFAULT_USERNAME_KEY, load_from_env=load_from_env)
        self.g['password_key'] = self.get_env('password_key', 'Key of password in environment',
                                              default=self.DEFAULT_PASSWORD_KEY, load_from_env=load_from_env)
        self.g['ping_timeout'] = self.get_env('ping_timeout', 'Maximum ping timeout in milliseconds',
                                              default=settings.DEFAULT_PING_TIMEOUT, load_from_env=load_from_env)


settings = Settings()
