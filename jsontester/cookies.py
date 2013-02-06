"""
Read cookies from chrome browser cookies
"""

import sys,os,configobj
from jsontester.sqlite import SQLiteDatabase

from requests import cookies

# Cookie paths:
# ~/Library/Application Support/Firefox/Profiles/toxwdvmv.default/cookies.sqlite
# ~/.firefox/Profiles/toxwdvmv.default/cookies.sqlite

if sys.platform=='darwin':
    CHROME_CONFIG_DIR = os.path.join(
        os.getenv('HOME'), 'Library','Application Support','Google','Chrome','Default'
    )
    FIREFOX_CONFIG_DIR = os.path.join(
        os.getenv('HOME'),'Library','Application Support','Firefox'
    )
elif sys.platform=='linux2':
    CHROME_CONFIG_DIR = None
    FIREFOX_CONFIG_DIR = os.path.join(os.getenv('HOME'),'.firefox')

class CookieError(Exception):
    def __str__(self):
        return self.args[0]

class BrowserSQLiteCookies(SQLiteDatabase):
    def __init__(self,browser,path):
        SQLiteDatabase.__init__(self,path)

class FirefoxCookies(BrowserSQLiteCookies):
    def __init__(self,configdir=None):
        self.configdir = configdir and configdir or FIREFOX_CONFIG_DIR
        if self.configdir is None:
            raise CookieError('Could not find firefox configuration directory')
        if not os.path.isdir(self.configdir):
            raise CookieError('No such directory: %s' % self.configdir)
        profile_path = self.get_profile_path()
        if profile_path is None:
            raise CookieError('Could not find firefox profile directory')
        path = os.path.join(self.configdir,profile_path,'cookies.sqlite')
        BrowserSQLiteCookies.__init__(self,'browser',path)

    def get_profile_path(self,name='default'):
        config = configobj.ConfigObj(os.path.join(self.configdir,'profiles.ini'))
        for section,items in config.items():
            if section[:7] != 'Profile' or 'Name' not in items:
                continue
            if items['Name'] == name:
                return items['Path']
        return None

    def lookup(self,host,name=None):
        c = self.cursor
        c.execute('select host,name,value from moz_cookies')

        if name is not None:
            c.execute("""SELECT name,value FROM moz_cookies WHERE host=? AND name=?""", (host,name,))
        else:
            c.execute("""SELECT name,value FROM moz_cookies WHERE host=?""", (host,))
        return dict((c[0],c[1]) for c in c.fetchall())

class ChromeCookies(BrowserSQLiteCookies):
    def __init__(self,configdir=None):
        self.configdir = configdir and configdir or CHROME_CONFIG_DIR
        if self.configdir is None:
            raise CookieError('Could not find chrome configuration directory')
        if not os.path.isdir(self.configdir):
            raise CookieError('No such directory: %s' % self.configdir)
        path = os.path.join(self.configdir,'Cookies')
        BrowserSQLiteCookies.__init__(self,'chrome',path)

    def lookup(self,host,name=None):
        c = self.cursor
        if name is not None:
            c.execute("""SELECT name,value FROM cookies WHERE host_key=? AND name=?""",(host,name,))
        else:
            c.execute("""SELECT name,value FROM cookies WHERE host_key=?""",(host,))
        return dict((c[0],c[1]) for c in c.fetchall())

def get_host_cookies(browser,host,name=None):
    if browser == 'firefox':
        cookies = FirefoxCookies()
    elif browser == 'chrome':
        cookies = ChromeCookies()
    else:
        raise CookieError('Unknown browser: %s' % browser)
    return cookies.lookup(host,name)

