"""
Request maker for json tester
"""

import requests
import urllib
import json
import string

from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth

from .responsecodes import response_code_text
from .log import Logger
from .cookies import get_host_cookies, CookieError

JSON_MIME = 'application/json'
DEFAULT_MAX_RETRIES = 3
DEFAULT_HEADERS = {
    'get': { 'Accept': JSON_MIME, },
    'post': { 'Content-Type': JSON_MIME, },
    'put': { 'Content-Type': JSON_MIME, },
    'delete': { 'Content-Type': JSON_MIME, },
}


class JSONRequestError(Exception):
    def __str__(self):
        return self.args[0]


class JSONRequest(object):
    def __init__(self, browser='chrome', retries=DEFAULT_MAX_RETRIES, username=None, password=None, verify=True):
        self.log = Logger('request').default_stream
        self.authentication = None
        self.browser = browser
        self.verify = verify
        if username and password:
            self.auth = HTTPBasicAuth(username, password)
        else:
            self.auth = None

        self.session = requests.Session()
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def __prepare_query__(self, name, url, extra_headers, cookies={}):
        if cookies is not {}:
            if self.browser is not None:
                host = urllib.splithost(url.lstrip(string.ascii_letters+':'))[0]
                if ':' in host:
                    host = host.split(':', 1)[0]
                try:
                    cookies = get_host_cookies(self.browser, host)
                except CookieError as e:
                    raise JSONRequestError(str(e))

        if name not in DEFAULT_HEADERS:
            return extra_headers, cookies

        headers = DEFAULT_HEADERS[name].copy()
        if extra_headers:
            headers.update(extra_headers)
        return headers, cookies

    def get(self, url, cookies={}, headers={}):
        headers, cookies = self.__prepare_query__('get', url, headers, cookies)
        try:
            res = requests.get(url, cookies=cookies, headers=headers, auth=self.auth, verify=self.verify)
        except requests.exceptions.ConnectionError as e:
            raise JSONRequestError('{0}'.format(e))
        else:
            return res

    def delete(self, url, cookies={}, headers={}):
        headers, cookies = self.__prepare_query__('delete', url, headers, cookies)
        try:
            res = requests.delete(url, cookies=cookies, headers=headers, auth=self.auth, verify=self.verify)
        except requests.exceptions.ConnectionError as e:
            raise JSONRequestError('{0}'.format(e))
        else:
            return res

    def post(self, url, data, cookies={}, headers={}):
        headers, cookies = self.__prepare_query__('post', url, headers, cookies)
        try:
            res = requests.post(url, data, cookies=cookies, headers=headers, auth=self.auth, verify=self.verify)
        except requests.exceptions.ConnectionError as e:
            raise JSONRequestError('{0}'.format(e))
        else:
            return res

    def put(self, url, data, cookies={}, headers={}):
        headers, cookies = self.__prepare_query__('put', url, headers, cookies)
        try:
            res = requests.put(url, data, cookies=cookies, headers=headers, auth=self.auth, verify=self.verify)
        except requests.exceptions.ConnectionError as e:
            raise JSONRequestError('{0}'.format(e))
        else:
            return res
