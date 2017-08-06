import requests
import os
import base64
import logging
import urllib.parse
import re


logger = logging.getLogger(__name__)

try:
    ASUS_API_USERNAME = os.environ['ASUS_API_USERNAME']
    ASUS_API_PASSWORD = os.environ['ASUS_API_PASSWORD']
except KeyError as e:
    from django.conf import settings
    # settings.configure()
    ASUS_API_USERNAME = getattr(settings, 'ASUS_API_USERNAME', None)
    ASUS_API_PASSWORD = getattr(settings, 'ASUS_API_PASSWORD', None)


class AsusApi:

    HOST = 'http://192.168.1.1/'

    def __init__(self, username=None, password=None):
        self.asus_token = AsusToken()
        self.username = username if username else ASUS_API_USERNAME
        self.password = password if password else ASUS_API_PASSWORD

    def login(self):
        """Logs in to the router using either conf.settings or env variables"""
        url = self._get_url('login.cgi')
        headers = {
            'Referer': 'http://192.168.1.1/Main_Login.asp',
        }
        data = {
            'login_authorization': self.get_credentials_b64_encoded()
        }
        req = requests.post(url, headers=headers, data=data)
        token_cookie_str = req.headers.get('Set-Cookie')
        self.asus_token = AsusToken.from_cookie_str(token_cookie_str)
        if not self.asus_token:
            logger.info('Login failed')

    def get_client_connections_status(self):
        url = self._get_url('Main_WStatus_Content.asp')

    def get_connected_clients(self):
        url = self._get_url('update_clients.asp')
        headers = {
            'Referer': 'http://192.168.1.1/Main_Login.asp',
        }
        res = requests.get(url, headers=headers)
        return self.parse_clients(res.content.decode('utf-8'))

    def block_client(self, clients):
        url = self._get_url('start_apply2.htm')

    def parse_clients(self, raw_clients_js):
        """
        Parses raw_clients_js blob wich is javascript
        :param raw_clients_js: client information in the form of raw javascript code
        :return: a list of Client objects
        """
        blocked_macs = []

        clients_unquoted = urllib.parse.unquote(raw_clients_js)
        for line in clients_unquoted.splitlines():
            if line.startswith('time_scheduling_mac'):
                print(line)
                macs_match = re.search(r"\('(?P<macs>[A-Z1-9:>]+)'\)", line)
                blocked_macs = macs_match.group('macs').split('>')
                print(blocked_macs)
                print('parse_clients')

    def get_credentials_b64_encoded(self):
        credentials_formatted = f'{self.username}:{self.password}'
        return base64.b64encode(credentials_formatted.encode('utf-8'))

    def _get_url(self, path):
        return f'{self.HOST}{path}'

    def __str__(self):
        return str(self.asus_token)


class AsusToken:
    def __init__(self, token=None):
        if token is not None:
            self.token = token
            self._save_token()
        else:
            self.token = self._load_token()

    @staticmethod
    def from_cookie_str(cookie_str):
        token_str = cookie_str.split(';')[0].split('=')[1] if cookie_str else ''
        return AsusToken(token_str)

    def _load_token(self):
        """Loads the asus api token and returns it"""
        try:
            with open(self._get_token_full_path(), 'r') as fh:
                return fh.readline().strip()
        except FileNotFoundError as e:
            logger.info(f'File not found {e.filename}')
            return ''

    def _save_token(self):
        """Saves the asus token for future use"""
        with open(self._get_token_full_path(), 'w') as fh:
            fh.write(self.token)

    def _get_token_full_path(self):
        return os.path.join(os.path.expanduser("~"), 'asus_token')

    def __str__(self):
        return self.token

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.token == other.token
        elif isinstance(other, str):
            return self.token == other
        raise NotImplementedError(f'Invalid rh type: {type(other)}')

    def __bool__(self):
        return bool(self.token)

    def __add__(self, other):
        return self.token + other

    def __radd__(self, other):
        return other + self.token


class Client:
    """Used to represent a client connected to the router"""
    def __init__(self, name, mac_addr, ip_addr, is_blocked):
        self.name = name
        self.mac_addr = mac_addr
        self.ip_addr = ip_addr
        self.is_blocked = is_blocked

    def __str__(self):
        return f'{self.name} (mac={self.mac_addr}  ip={self.ip_addr} blocked={self.is_blocked})'

if __name__ == '__main__':
    # api = AsusApi('bob', 'brown')
    # print(f'before: {api}')
    # api.login()
    # print(f'after: {api}')
    api = AsusApi()
    clients_raw = api.get_connected_clients()
    # print(clients_raw)

