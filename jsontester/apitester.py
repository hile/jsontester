"""
API testing tools
"""

from .shell import ScriptThread

class JSONAPI(object):
    def __init__(self,url):
        self.url = url

class APITestThread(ScriptThread):
    def __init__(self,config):
        ScriptThread.__init__(self,'jsontester')
        self.config = config

