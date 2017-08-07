from django.test import SimpleTestCase

import os
from unittest.mock import Mock, patch

from ..asus_router import AsusApi, AsusToken, Client, ClientConnectionSample


class TestAsusToken(SimpleTestCase):
    def setUp(self):
        self.test_token_str = '7860691732068997083136838469969'
        self.test_token = AsusToken(self.test_token_str)

    def test_token_str_is_empty_when_file_is_empty(self):
        with open(self.test_token._get_token_full_path(), 'w') as fh:
            fh.write('')
        token = AsusToken()
        self.assertEqual(token, '')

    def test_token_str_is_correctly_set_when_file_has_token_str(self):
        with open(self.test_token._get_token_full_path(), 'w') as fh:
            fh.write(self.test_token_str)
        self.assertEqual(AsusToken(), self.test_token_str)

    def test_token_gets_set_when_passed_in_init(self):
        token = AsusToken('1234abcd')
        self.assertEqual(token.token, '1234abcd')

    def test_token_gets_saved_when_passed_in_init(self):
        with open(self.test_token._get_token_full_path(), 'w') as fh:
            fh.write('')
        token = AsusToken('1234abcd')
        with open(self.test_token._get_token_full_path(), 'r') as fh:
            self.assertEqual(fh.readline().strip(), '1234abcd')

    def test__load_token_file_not_found(self):
        try:
            os.remove(self.test_token._get_token_full_path())
        except Exception as e:
            pass
        self.assertEqual(self.test_token._load_token(), '')

    def test__load_token_normal_token_str(self):
        with open(self.test_token._get_token_full_path(), 'w') as fh:
            fh.write(self.test_token_str)
        self.assertEqual(self.test_token._load_token(), self.test_token_str)

    def test__save_token_normal(self):
        try:
            os.remove(self.test_token._get_token_full_path())
        except Exception as e:
            pass
        self.test_token._save_token()
        with open(self.test_token._get_token_full_path(), 'r') as fh:
            self.assertEqual(fh.readline().strip(), self.test_token_str)

    def test_token__str__(self):
        token = AsusToken()
        token.token = self.test_token_str
        self.assertTrue(str(token) == self.test_token_str)

    def test_token__eq__with_str(self):
        token = AsusToken()
        token.token = self.test_token_str
        self.assertTrue(token == self.test_token_str)

    def test_token__eq__with_token(self):
        token1 = AsusToken(self.test_token_str)
        token2 = AsusToken(self.test_token_str)
        token1.token = 'abc'
        self.assertFalse(token1 == token2)

    def test_token__add__(self):
        cookie_format = 'asus_token: {};'
        self.assertEqual(cookie_format.format(self.test_token), cookie_format.format(self.test_token_str))

    def test_token__radd__(self):
        self.assertEqual('b'+self.test_token, 'b'+self.test_token_str)

    def test_from_cookie_str(self):
        cookie_str = 'asus_token=1070711480134875637378320976216; HttpOnly;'
        token = AsusToken.from_cookie_str(cookie_str)
        self.assertEqual(token, '1070711480134875637378320976216')


class TestAsusApi(SimpleTestCase):

    def setUp(self):
        self.test_token_str = '7860691732068997083136838469969'
        self.test_token = AsusToken(self.test_token_str)
        self.api = AsusApi()

    def test_asus_token_set_correctly_on_init(self):
        self.assertEqual(self.api.asus_token, self.test_token_str)

    def test_get_credentials_b64_encoded(self):
        api = AsusApi('bob', 'brown')
        self.assertEqual(api.get_credentials_b64_encoded(), b'Ym9iOmJyb3du')

    def test_username_and_password_set_when_passed_in(self):
        api = AsusApi('boy', 'george')
        self.assertEqual(api.username, 'boy')
        self.assertEqual(api.password, 'george')

    @patch('requests.post')
    def test_login_invalid_credentials(self, mock_post):
        mock_post.return_value.headers = {'Set-Cookie': ''}
        api = AsusApi('boy', 'george123')
        api.login()
        self.assertEqual(api.asus_token, '')

    @patch('requests.post')
    def test_login_valid_credentials(self, mock_post):
        """Requires that valid credentials are set either in config or env"""
        mock_post.return_value.headers = {'Set-Cookie': 'asus_token=1070711480134875637378320976216; HttpOnly;'}
        api = AsusApi()
        api.login()
        self.assertEqual(api.asus_token, '1070711480134875637378320976216')

    def test_parse_blocked_macs_0_blocked(self):
        with open('wifimanager/test/test_res/update_clients_none_blocked', 'r') as fh:
            text = fh.readlines()
        blocked_macs = AsusApi.parse_blocked_macs(''.join(text))
        self.assertListEqual(blocked_macs, [])

    def test_parse_blocked_macs_1_blocked(self):
        with open('wifimanager/test/test_res/update_clients_1_blocked', 'r') as fh:
            text = fh.readlines()
        blocked_macs = AsusApi.parse_blocked_macs(''.join(text))
        self.assertListEqual(blocked_macs, ['FC:C2:DE:53:BA:96'])

    def test_parse_blocked_macs_2_blocked(self):
        with open('wifimanager/test/test_res/update_clients_2_blocked', 'r') as fh:
            text = fh.readlines()
        blocked_macs = AsusApi.parse_blocked_macs(''.join(text))
        self.assertListEqual(blocked_macs, ['FC:C2:DE:53:BA:96', '68:37:E9:1D:A7:CE'])

    def test_fromnetworkmapd_no_clients(self):
        with open('wifimanager/test/test_res/update_clients_no_clients', 'r') as fh:
            text = fh.readlines()
        clients = AsusApi.parse_fromnetworkmapd(''.join(text))
        self.assertListEqual(clients, [])

    def test_fromnetworkmapd_multiple_clients(self):
        with open('wifimanager/test/test_res/update_clients_multiple_clients', 'r') as fh:
            text = fh.readlines()
        clients = AsusApi.parse_fromnetworkmapd(''.join(text))
        expected = [
            ('android-1964d212bfe2cad', '192.168.1.96', '9C:D9:17:85:1A:5C'),
            ('android-2cf34b28e2eecd6f', '192.168.1.116', 'FC:C2:DE:53:BA:96'),
            ('android-3e49f060dd4f692f', '192.168.1.219', 'DC:0B:34:97:C8:69'),
            ('amazon-e9064d55c', '192.168.1.198', 'B4:7C:9C:C5:50:31'),
            ('LoganHahsiPhone', '192.168.1.157', 'A4:B8:05:D8:64:DD'),
            ('amazon-b1f569309', '192.168.1.235', 'AC:63:BE:B6:74:36')
        ]
        self.assertListEqual(clients, expected)

    def test_parse_clients_no_clients(self):
        with open('wifimanager/test/test_res/update_clients_no_clients', 'r') as fh:
            text = fh.readlines()
        clients = AsusApi.parse_clients(''.join(text))
        self.assertListEqual(clients, [])

    def test_parse_clients_1_client_blocked(self):
        with open('wifimanager/test/test_res/update_clients_1_blocked', 'r') as fh:
            text = fh.readlines()
        clients = AsusApi.parse_clients(''.join(text))
        self.assertEqual(len([client for client in clients if client.is_blocked and client.mac_addr == 'FC:C2:DE:53:BA:96']), 1)

    def test_parse_clients_multiple_clients(self):
        with open('wifimanager/test/test_res/update_clients_multiple_clients', 'r') as fh:
            text = fh.readlines()
        clients = AsusApi.parse_clients(''.join(text))
        expected = [
            Client('android-1964d212bfe2cad', '9C:D9:17:85:1A:5C', '192.168.1.96', False),
            Client('android-2cf34b28e2eecd6f', 'FC:C2:DE:53:BA:96', '192.168.1.116', False),
            Client('android-3e49f060dd4f692f', 'DC:0B:34:97:C8:69', '192.168.1.219', False),
            Client('amazon-e9064d55c', 'B4:7C:9C:C5:50:31', '192.168.1.198', False),
            Client('LoganHahsiPhone', 'A4:B8:05:D8:64:DD', '192.168.1.157', False),
            Client('amazon-b1f569309', 'AC:63:BE:B6:74:36', '192.168.1.235', False)
        ]
        self.assertListEqual(clients, expected)

    @patch('requests.get')
    def test_get_client_connection_statuses_multiple_clients(self, mock_get):
        with open('wifimanager/test/test_res/client_connection_statuses.html', 'rb') as fh:
            html_content = fh.read()
        mock_get.return_value.content = html_content
        api = AsusApi()
        expected = [
            ClientConnectionSample('34:DE:1A:01:A1:E9', '-60dBm', '121.5M', '6.5M', '00:01:42'),
            ClientConnectionSample('DC:0B:34:97:C8:69', '-69dBm', '26M', '6.5M', '00:06:00'),
            ClientConnectionSample('FC:C2:DE:53:BA:96', '-65dBm', '1M', '24M', '01:24:12')
        ]
        client_statuses = api.get_client_connection_statuses()
        self.assertListEqual(client_statuses, expected)

    @patch('requests.get')
    def test_get_client_connection_statuses_no_clients(self, mock_get):
        with open('wifimanager/test/test_res/client_connection_statuses_no_connections.html', 'rb') as fh:
            html_content = fh.read()
        mock_get.return_value.content = html_content
        api = AsusApi()
        client_statuses = api.get_client_connection_statuses()
        self.assertListEqual(client_statuses, [])

    def test_build_block_clientlist_str_no_clients(self):
        api = AsusApi()
        data = api.build_block_clients_data([])
        self.assertEqual(data['MULTIFILTER_DEVICENAME'], '')
        self.assertEqual(data['MULTIFILTER_ENABLE'], '')
        self.assertEqual(data['MULTIFILTER_MAC'], '')
        self.assertEqual(data['MULTIFILTER_MACFILTER_DAYTIME'], '')
        self.assertEqual(data['custom_clientlist'], '')

    def test_build_block_clientlist_str_1_client(self):
        api = AsusApi()
        data = api.build_block_clients_data(['FC:C2:DE:53:BA:96'])
        self.assertEqual(data['MULTIFILTER_DEVICENAME'], 'boogie')
        self.assertEqual(data['MULTIFILTER_ENABLE'], '1')
        self.assertEqual(data['MULTIFILTER_MAC'], 'FC:C2:DE:53:BA:96')
        self.assertEqual(data['MULTIFILTER_MACFILTER_DAYTIME'], '<')
        self.assertEqual(data['custom_clientlist'], '<boogie>FC:C2:DE:53:BA:96>0>0>>')

    def test_build_block_clientlist_str_3_client(self):
        api = AsusApi()
        data = api.build_block_clients_data(['FC:C2:DE:53:BA:96', 'AC:63:BE:B6:74:36', '68:37:E9:1D:A7:CE'])
        self.assertEqual(data['MULTIFILTER_DEVICENAME'], 'boogie>boogie>boogie')
        self.assertEqual(data['MULTIFILTER_ENABLE'], '1>1>1')
        self.assertEqual(data['MULTIFILTER_MAC'], 'FC:C2:DE:53:BA:96>AC:63:BE:B6:74:36>68:37:E9:1D:A7:CE')
        self.assertEqual(data['MULTIFILTER_MACFILTER_DAYTIME'], '<><><')
        self.assertEqual(data['custom_clientlist'], '<boogie>FC:C2:DE:53:BA:96>0>0>><boogie>AC:63:BE:B6:74:36>0>0>><boogie>68:37:E9:1D:A7:CE>0>0>>')

