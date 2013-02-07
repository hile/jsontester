"""
Request maker for json tester
"""

import requests,urllib,json,string
from responsecodes import response_code_text

from jsontester.log import Logger
from jsontester.cookies import get_host_cookies,CookieError

JSON_MIME = 'application/json'
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
    def __init__(self,browser='chrome'):
        self.log = Logger('request').default_stream
        self.authentication = None
        self.browser = browser

    def __prepare_query__(self,name,url,extra_headers,cookies={}):
        if cookies is not {}:
            if self.browser is not None:
                host = urllib.splithost(url.lstrip(string.ascii_letters+':'))[0]
                if ':' in host:
                    host = host.split(':',1)[0]
                try:
                    cookies = get_host_cookies(self.browser,host)
                except CookieError,emsg:
                    raise JSONRequestError(str(emsg))

        if name not in DEFAULT_HEADERS:
            return extra_headers,cookies

        headers = DEFAULT_HEADERS[name].copy()
        headers.update(extra_headers)
        return headers,cookies

    def get(self,url,cookies={},headers={}):
        headers,cookies = self.__prepare_query__('get',url,headers,cookies)
        res = requests.get(url,cookies=cookies,headers=headers)
        return res

    def delete(self,url,cookies={},headers={}):
        headers,cookies = self.__prepare_query__('delete',url,headers,cookies)
        res = requests.delete(url,cookies=cookies,headers=headers)
        return res

    def post(self,url,data,cookies={},headers={}):
        headers,cookies = self.__prepare_query__('post',url,headers,cookies)
        res = requests.post(url,data,cookies=cookies,headers=headers)
        return res

    def put(self,url,data,cookies={},headers={}):
        headers,cookies = self.__prepare_query__('put',url,headers,cookies)
        res = requests.put(url,data,cookies=cookies,headers=headers)
        return res
