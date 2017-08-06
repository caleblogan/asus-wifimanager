from django.test import SimpleTestCase

import os
from unittest.mock import Mock, patch

from .asus_router import AsusApi, AsusToken


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
