# coding=utf-8
"""
Logging from scripts and parser for syslog files
"""

import os
import sys
import fnmatch
import re
import urllib
import bz2
import gzip
import threading
import logging
import logging.handlers

from datetime import datetime, timedelta

DEFAULT_LOGFORMAT = '%(module)s %(levelname)s %(message)s'
DEFAULT_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOGFILEFORMAT = '%(asctime)s %(module)s.%(funcName)s %(message)s'
DEFAULT_LOGSIZE_LIMIT = 2**20
DEFAULT_LOG_BACKUPS = 10

DEFAULT_SYSLOG_FORMAT = '%(message)s'
DEFAULT_SYSLOG_LEVEL =  logging.handlers.SysLogHandler.LOG_WARNING
DEFAULT_SYSLOG_FACILITY = logging.handlers.SysLogHandler.LOG_USER

# Mapping to set syslog handler levels via same classes as normal handlers
LOGGING_LEVEL_NAMES = ( 'DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL')
SYSLOG_LEVEL_MAP = {
    logging.handlers.SysLogHandler.LOG_DEBUG:   logging.DEBUG,
    logging.handlers.SysLogHandler.LOG_NOTICE:  logging.INFO,
    logging.handlers.SysLogHandler.LOG_INFO:    logging.INFO,
    logging.handlers.SysLogHandler.LOG_WARNING: logging.WARN,
    logging.handlers.SysLogHandler.LOG_ERR:     logging.ERROR,
    logging.handlers.SysLogHandler.LOG_CRIT:    logging.CRITICAL,
}

# Local syslog device varies by platform
if sys.platform == 'linux2' or fnmatch.fnmatch(sys.platform, '*bsd*'):
    DEFAULT_SYSLOG_ADDRESS = '/dev/log'
elif sys.platform == 'darwin':
    DEFAULT_SYSLOG_ADDRESS = '/var/run/syslog'
else:
    DEFAULT_SYSLOG_ADDRESS = ( 'localhost', 514 )


# Default matchers for syslog entry 'host, program, pid' parts
SOURCE_FORMATS = [
    re.compile('^<(?P<version>[^>]+)>\s+(?P<host>[^\s]+)\s+(?P<program>[^\[]+)\[(?P<pid>\d+)\]$'),
    re.compile('^<(?P<version>[^>]+)>\s+(?P<host>[^\s]+)\s+(?P<program>[^\[]+)$'),
    re.compile('^<(?P<facility>\d+)\.(?P<level>\d+)>\s+(?P<host>[^\s]+)\s+(?P<program>[^\[]+)\[(?P<pid>\d+)\]$'),
    re.compile('^<(?P<facility>\d+)\.(?P<level>\d+)>\s+(?P<host>[^\s]+)\s+(?P<program>[^\[]+)$'),
    re.compile('^(?P<host>[^\s]+)\s+(?P<program>[^\[]+)\[(?P<pid>\d+)\]$'),
    re.compile('^(?P<host>[^\s]+)\s+(?P<program>[^\[]+)$'),
]


class LoggerError(Exception):
    """
    Exceptions raised by logging configuration
    """
    pass


class Logger(object):
    """
    Singleton class for common logging tasks.
    """
    __instances = {}
    def __init__(self, name=None, logformat=DEFAULT_LOGFORMAT, timeformat=DEFAULT_TIME_FORMAT):
        name = name is not None and name or self.__class__.__name__
        thread_id = threading.current_thread().ident
        if thread_id is not None:
            name = '{0}-{1}'.format(thread_id, name)

        if not Logger.__instances.has_key(name):
            Logger.__instances[name] = Logger.LoggerInstance(name, logformat, timeformat)

        self.__dict__['_Logger__instances'] = Logger.__instances
        self.__dict__['name'] = name

    class LoggerInstance(dict):
        """
        Singleton implementation of logging configuration for one program
        """
        def __init__(self, name, logformat, timeformat):
            self.name = name
            self.level = logging.Logger.root.level
            self.register_stream_handler('default_stream', logformat, timeformat)

        def __getattr__(self, attr):
            if attr in self.keys():
                return self[attr]
            raise AttributeError('No such LoggerInstance log handler: {0}'.format(attr))

        def __get_or_create_logger__(self, name):
            if name not in self.keys():
                for logging_manager in logging.Logger.manager.loggerDict.values():
                    if hasattr(logging_manager, 'name') and logging_manager.name==name:
                        self[name] = logging.getLogger(name)
                        break

            if name not in self.keys():
                self[name] = logging.getLogger(name)

            return self[name]

        def __match_handlers__(self, handler_list, handler):
            def match_handler(a, b):
                if type(a) != type(b):
                    return False

                if isinstance(a, logging.StreamHandler):
                    for k in ('stream', 'name',):
                        if getattr(a, k) != getattr(b, k):
                            return False
                    return True

                if isinstance(a, logging.handlers.SysLogHandler):
                    for k in ( 'address', 'facility', ):
                        if getattr(a, k) != getattr(b, k):
                            return False
                    return True

                if isinstance(a, logging.handlers.HTTPHandler):
                    for k in ( 'host', 'url', 'method', ):
                        if getattr(a, k) != getattr(b, k):
                            return False
                    return True

                return True

            if not isinstance(handler, logging.Handler):
                raise LoggerError('Not an instance of logging.Handler: {0}'.format(handler))

            if not isinstance(handler_list, list):
                raise LoggerError('BUG handler_list must be a list instance')

            for match in handler_list:
                if match_handler(match, handler):
                    return True

            return False

        def register_stream_handler(self, name, logformat=None, timeformat=None):
            if logformat is None:
                logformat = DEFAULT_LOGFORMAT
            if timeformat is None:
                timeformat = DEFAULT_TIME_FORMAT

            logger = self.__get_or_create_logger__(name)
            handler = logging.StreamHandler()
            if self.__match_handlers__(self.default_stream.handlers, handler):
                return

            if not self.__match_handlers__(logger.handlers, handler):
                handler.setFormatter(logging.Formatter(logformat, timeformat))
                logger.addHandler(handler)

            return logger

        def register_syslog_handler(self, name,
                address=DEFAULT_SYSLOG_ADDRESS,
                facility=DEFAULT_SYSLOG_FACILITY,
                default_level=DEFAULT_SYSLOG_LEVEL,
                socktype=None,
                logformat=None,
            ):

            if logformat is None:
                logformat = DEFAULT_SYSLOG_FORMAT

            if default_level not in SYSLOG_LEVEL_MAP.keys():
                raise LoggerError('Unsupported syslog level value')

            logger = self.__get_or_create_logger__(name)
            handler = logging.handlers.SysLogHandler(address, facility, socktype)
            handler.level = default_level
            if not self.__match_handlers__(logger.handlers, handler):
                handler.setFormatter(logging.Formatter(logformat))
                logger.addHandler(handler)
                logger.setLevel(self.loglevel)

            return logger

        def register_http_handler(self, name, url, method='POST'):
            logger = self.__get_or_create_logger__(name)
            try:
                host, path = urllib.splithost(url[url.index(':')+1:])
            except IndexError as e:
                raise LoggerError('Error parsing URL {0}: {1}'.format(url, e))

            handler = logging.handlers.HTTPHandler(host, url, method)
            if not self.__match_handlers__(logger.handlers, handler):
                logger.addHandler(handler)
                logger.setLevel(self.loglevel)

            return logger

        def register_file_handler(self, name, directory,
                         filename=None,
                         logformat=None,
                         timeformat=None,
                         maxBytes=DEFAULT_LOGSIZE_LIMIT,
                         backupCount=DEFAULT_LOG_BACKUPS):

            if filename is None:
                filename = '{0}.log'.format(name)
            if logformat is None:
                logformat = DEFAULT_LOGFILEFORMAT
            if timeformat is None:
                timeformat = DEFAULT_TIME_FORMAT

            if not os.path.isdir(directory):
                try:
                    os.makedirs(directory)
                except OSError:
                    raise LoggerError('Error creating directory: {0}'.format(directory))
            logfile = os.path.join(directory, filename)

            logger = self.__get_or_create_logger__(name)
            handler = logging.handlers.RotatingFileHandler(
                filename=logfile,
                mode='a+',
                maxBytes=maxBytes,
                backupCount=backupCount
            )
            if not self.__match_handlers__(logger.handlers, handler):
                handler.setFormatter(logging.Formatter(logformat, timeformat))
                logger.addHandler(handler)
                logger.setLevel(self.loglevel)

            return logger

        @property
        def level(self):
            return self._level
        @level.setter
        def level(self, value):
            if not isinstance(value, int):
                if value in LOGGING_LEVEL_NAMES:
                    value = getattr(logging, value)
                try:
                    value = int(value)
                    if value not in SYSLOG_LEVEL_MAP.values():
                        raise ValueError
                except ValueError:
                    raise ValueError('Invalid logging level value: {0}'.format(value))

            for logger in self.values():
                if hasattr(logger, 'setLevel'):
                    logger.setLevel(value)
            self._level = value

        # Compatibility for old API
        @property
        def loglevel(self):
            return self.level
        @loglevel.setter
        def loglevel(self, value):
            self.level = value

        # compatibility for old API
        def set_level(self, value):
            self.level = value

    def __getattr__(self, attr):
        return getattr(self.__instances[self.name], attr)

    def __setattr__(self, attr, value):
        setattr(self.__instances[self.name], attr, value)

    def __getitem__(self, item):
        return self.__instances[self.name][item]

    def __setitem__(self, item, value):
        self.__instances[self.name][item] = value

    def register_stream_handler(self, name, logformat=None, timeformat=None):
        """
        Register a common log stream handler
        """
        return self.__instances[self.name].register_stream_handler(
            name, logformat, timeformat
        )

    def register_syslog_handler(self, name,
            address=DEFAULT_SYSLOG_ADDRESS,
            facility=DEFAULT_SYSLOG_FACILITY,
            default_level=DEFAULT_SYSLOG_LEVEL,
            socktype=None,
            logformat=None,
        ):
        """Register syslog handler

        Register handler for syslog messages

        """
        return self.__instances[self.name].register_syslog_handler(
            name, address, facility, default_level, socktype, logformat
        )

    def register_http_handler(self, name, url, method='POST'):
        """Register HTTP handler

        Register a HTTP POST logging handler

        """
        return self.__instances[self.name].register_http_handler(
            name, url, method
        )

    def register_file_handler(self, name, directory,
                     filename=None,
                     logformat=None,
                     timeformat=None,
                     maxBytes=DEFAULT_LOGSIZE_LIMIT,
                     backupCount=DEFAULT_LOG_BACKUPS):
        """Register log file handler

        Register a common log file handler for rotating file based logs

        """
        return self.__instances[self.name].register_file_handler(
            name, directory, filename, logformat, timeformat, maxBytes, backupCount
        )
