import requests
import os
import base64
import logging
import urllib.parse
import re
from datetime import datetime
from bs4 import BeautifulSoup


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

    def get_client_connection_statuses(self):
        url = self._get_url('Main_WStatus_Content.asp')
        headers = {
            'Referer': 'http://192.168.1.1/Main_Login.asp',
            'Cookie': f'asus_token={self.asus_token}'
        }
        res = requests.get(url, headers=headers)
        print(res.content.decode('utf-8'))
        return self.parse_client_connection_html(res.content.decode('utf-8'))

    def get_connected_clients(self):
        url = self._get_url('update_clients.asp')
        headers = {
            'Referer': 'http://192.168.1.1/Main_Login.asp',
        }
        res = requests.get(url, headers=headers)
        return self.parse_clients(res.content.decode('utf-8'))

    def block_client(self, clients):
        url = self._get_url('start_apply2.htm')

    @classmethod
    def parse_client_connection_html(cls, connections_html):
        connection_samples = []
        soup = BeautifulSoup(connections_html, 'html.parser')
        text_area_content = soup.textarea.get_text().split('idx MAC')[1]
        for sample in text_area_content.splitlines():
            if 'Associated Authorized' not in sample and sample.strip():
                new_sample = ClientConnectionSample.from_raw_sample_text(sample)
                connection_samples.append(new_sample)
        return connection_samples

    @classmethod
    def parse_clients(cls, raw_clients_js):
        """
        Parses raw_clients_js blob wich is javascript
        :param raw_clients_js: client information in the form of raw javascript code
        :return: a list of Client objects
        """
        clients_js_unquoted = urllib.parse.unquote(raw_clients_js)
        clients = []
        blocked_macs = cls.parse_blocked_macs(clients_js_unquoted)
        for name, ip, mac in cls.parse_fromnetworkmapd(clients_js_unquoted):
            is_blocked = True if mac in blocked_macs else False
            clients.append(Client(name, mac, ip, is_blocked))

        return clients

    @staticmethod
    def parse_fromnetworkmapd(raw_clients_js):
        """
        Takes in raw_clients_js and returns a list of tuples representing partial clients data
        Tuple format (device_name, ip_addr, mac_addr)
        :param raw_clients_js:
        :return: A list of tuples containing data about clients
        """
        clients = []
        for line in raw_clients_js.splitlines():
            if line.startswith('fromNetworkmapd'):
                for clients_raw in line.split('<0>'):
                    client_fields = clients_raw.split('>')
                    if len(client_fields) > 2:
                        clients.append(tuple(client_fields[0:3]))
                break
        return clients

    @staticmethod
    def parse_blocked_macs(raw_clients_js):
        """Takes in a text blob of clients js and returns a list of blocked macs"""
        blocked_macs = []
        for line in raw_clients_js.splitlines():
            if line.startswith('time_scheduling_mac'):
                macs_match = re.search(r"\('(?P<macs>[A-Z1-9:>]{2,})'\)", line)
                if macs_match:
                    blocked_macs = macs_match.group('macs').split('>')
        return blocked_macs

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


class ClientConnectionSample:
    """A sample of a clients connection at a point in time."""
    def __init__(self, mac_addr, rssi, tx_rate, rx_rate, connection_time):
        self.mac_addr = mac_addr
        self.rssi = rssi
        self.tx_rate = tx_rate
        self.rx_rate = rx_rate
        self.connection_time = connection_time
        self.sample_time = datetime.now()

    @classmethod
    def from_raw_sample_text(self, sample_text):
        stripped_sample = re.subn(' +', ' ', sample_text)[0].strip()
        if stripped_sample:
            mac, *_, rssi, __, tx, rx, connection_time = stripped_sample.split(' ')
            return ClientConnectionSample(mac, rssi, tx, rx, connection_time)
        return None

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f'{self.mac_addr} (tx={self.tx_rate} rx={self.rx_rate})'


class Client:
    """Used to represent a client connected to the router"""
    def __init__(self, name, mac_addr, ip_addr, is_blocked):
        self.name = name
        self.mac_addr = mac_addr
        self.ip_addr = ip_addr
        self.is_blocked = is_blocked

    def __repr__(self):
        return str(self)

    def __str__(self):
        return f'{self.name} (mac={self.mac_addr}  ip={self.ip_addr} blocked={self.is_blocked})'

    def __eq__(self, other):
        return (self.name == other.name and
                self.mac_addr == other.mac_addr and
                self.ip_addr == other.ip_addr and
                self.is_blocked == other.is_blocked)

if __name__ == '__main__':
    asus = AsusApi()
    # connected_clients = asus.get_connected_clients()
    # print('blocked:', [blocked_client for blocked_client in connected_clients if blocked_client.is_blocked])
    # for client in connected_clients:
    #     print(client)
    asus.login()
    connections_info = asus.get_client_connection_statuses()
    print(connections_info)
    # for status in connections_info:
    #     print(status)

