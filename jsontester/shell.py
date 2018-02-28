#!/usr/bin/env python
"""
Utility functions for python in unix shell.
"""

import sys
import os
import time
import signal
import socket
import argparse
import threading
import unicodedata

from subprocess import check_output, CalledProcessError, Popen, PIPE
from setproctitle import setproctitle

from .log import Logger

class ScriptError(Exception):
    pass


class CommandPathCache(list):
    """
    Class to represent commands on user's search path.
    """
    def __init__(self):
        self.update()

    def update(self):
        """
        Updates the commands available on user's PATH
        """
        paths = []
        self.__delslice__(0, len(self))

        for path in os.getenv('PATH').split(os.pathsep):
            if not paths.count(path):
                paths.append(path)

        for path in paths:
            if not os.path.isdir(path):
                continue
            for cmd in [os.path.join(path, f) for f in os.listdir(path)]:
                if os.path.isdir(cmd) or not os.access(cmd, os.X_OK):
                    continue
                self.append(cmd)

    def versions(self, name):
        """
        Returns all commands with given name on path, ordered by PATH search
        order.
        """
        if not len(self):
            self.update()
        return filter(lambda x: os.path.basename(x) == name, self)

    def which(self, name):
        """
        Return first matching path to command given with name, or None if
        command is not on path
        """
        if not len(self):
            self.update()
        try:
            return filter(lambda x: os.path.basename(x) == name, self)[0]
        except IndexError:
            return None


class ScriptThread(threading.Thread):
    """
    Common script thread base class
    """
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.log = Logger(name).default_stream
        self.status = 'not running'
        self.setDaemon(True)
        self.setName(name)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    @property
    def stopped(self):
        return self._stop_event.isSet()

    def execute(self, command):
        p = subprocess.Popen(command, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        return p.wait()


class Script(object):
    """
    Class for common CLI tool script
    """
    def __init__(self, name=None, description=None, epilog=None, debug_flag=True):
        self.name = os.path.basename(sys.argv[0])
        setproctitle('{0} {1}'.format(self.name, ' '.join(sys.argv[1:])))
        signal.signal(signal.SIGINT, self.SIGINT)

        reload(sys)
        sys.setdefaultencoding('utf-8')

        if name is None:
            name = self.name

        # Set to True to avoid any messages from self.message to be printed
        self.silent = False

        self.logger = Logger(self.name)
        self.log = self.logger.default_stream

        self.subcommand_parser = None
        self.parser = argparse.ArgumentParser(
            prog=name,
            description=description,
            formatter_class=argparse.RawTextHelpFormatter,
            epilog=epilog,
            add_help=True,
            conflict_handler='resolve',
        )
        if debug_flag:
            self.parser.add_argument('--debug', action='store_true', help='Show debug messages')

        self.parser.add_argument('-H', '--headers', action='append', help='Extra headers to send')
        self.parser.add_argument('-u', '--username', help='Basic auth username')
        self.parser.add_argument('-p', '--password', help='Basic auth password')
        self.parser.add_argument('--insecure', action='store_false', help='No HTTPS certificate validation')
        self.parser.add_argument('-B', '--browser',
            choices=('chrome','chromium','firefox'),
            help='Browser for cookie stealing'
        )

    def SIGINT(self, signum, frame):
        """
        Parse SIGINT signal by quitting the program cleanly with exit code 1
        """
        for t in filter(lambda t: t.name!='MainThread', threading.enumerate()):
            t.stop()
        for t in filter(lambda t: t.name!='MainThread', threading.enumerate()):
            t.join()
        self.exit(1)

    def wait(self, poll_interval=1):
        """
        Wait for running threads to finish.
        Poll interval is time to wait between checks for threads
        """
        while True:
            active = filter(lambda t: t.name!='MainThread', threading.enumerate())
            if not len(active):
                break
            self.log.debug('Waiting for {0} threads'.format(len(active)))
            time.sleep(poll_interval)

    def exit(self, value=0, message=None):
        """
        Exit the script with given exit value.
        If message is not None, it is printed on screen.
        """
        if isinstance(value, bool):
            if value:
                value = 0
            else:
                value = 1
        else:
            try:
                value = int(value)
                if value < 0 or value > 255:
                    raise ValueError
            except ValueError:
                value = 1

        if message is not None:
            self.message(message)

        for t in filter(lambda t: t.name!='MainThread', threading.enumerate()):
            t.stop()

        while True:
            active = filter(lambda t: t.name!='MainThread', threading.enumerate())
            if not len(active):
                break
            time.sleep(1)

        sys.exit(value)

    def message(self, message):
        if self.silent:
            return
        sys.stdout.write('{0}\n'.format(message))

    def error(self, message):
        sys.stderr.write('{0}\n'.format(message))

    def add_subcommand(self, command):
        """Add a subcommand parser instance

        Register named subcommand parser to argument parser

        Subcommand parser must be an instance of ScriptCommand class.

        Example usage:

        class ListCommand(ScriptCommand):
            def run(self, args):
                print('Listing stuff')

        parser.add_subcommand(ListCommand('list', 'List stuff from script'))

        """

        if self.subcommand_parser is None:
            self.subcommand_parser = self.parser.add_subparsers(
                dest='command', help='Please select one command mode below',
                title='Command modes'
            )
            self.subcommands = {}

        if not isinstance(command, ScriptCommand):
            raise ScriptError('Subcommand must be a ScriptCommand instance')

        parser = self.subcommand_parser.add_parser(
            command.name,
            help=command.short_description,
            description=command.description,
            epilog=command.epilog,
            formatter_class=argparse.RawTextHelpFormatter,
        )
        self.subcommands[command.name] = command
        command.script = self

        return parser

    def usage_error(self, *args, **kwargs):
        return self.parser.error(*args, **kwargs)

    def add_argument(self, *args, **kwargs):
        """
        Shortcut to add argument to main argumentparser instance
        """
        self.parser.add_argument(*args, **kwargs)

    def parse_args(self):
        """
        Call parse_args for parser and check for default logging flags
        """
        args = self.parser.parse_args()

        if hasattr(args, 'debug') and getattr(args, 'debug'):
            self.logger.set_level('DEBUG')

        elif hasattr(args, 'quiet') and getattr(args, 'quiet'):
            self.silent = True

        elif hasattr(args, 'verbose') and getattr(args, 'verbose'):
            self.logger.set_level('INFO')

        if self.subcommand_parser is not None:
            self.subcommands[args.command].run(args)

        return args

    def execute(self, args, dryrun=False):
        """
        Default wrapper to execute given interactive shell command
        with standard stdin, stdout and stderr
        """
        if isinstance(args, basestring):
            args = args.split()

        if not isinstance(args, list):
            raise ValueError('Execute arguments must be a list')

        if dryrun:
            self.log.debug('would execute: {0}'.format(' '.join(args)))
            return 0

        p = Popen(args, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        p.wait()
        return p.returncode

    def check_output(self, args):
        """
        Wrapper for subprocess.check_output to be executed in script context
        """
        if isinstance(args, basestring):
            args = [args]
        try:
            return check_output(args)

        except IOError as e:
            raise ScriptError(e)

        except OSError as e:
            raise ScriptError(e)

        except CalledProcessError as e:
            raise ScriptError(e)


class ScriptCommand(argparse.ArgumentParser):
    """Script subcommand parser class

    Parser for Script subcommands.

    Implement custom logic to this class and provide a custom
    parse_args to call these methods as required

    """
    def __init__(self, name, short_description='', description='', epilog=''):
        self.script = None
        self.name = name
        self.short_description = short_description
        self.description = description
        self.epilog = epilog

    def run(self, args):
        """Run subcommands

        This method is called from parent script parse_args with
        processed arguments, when a subcommand has been registered

        Implement your subcommand logic here.

        """
        sys.stderr.write('Subcommand {0} has no run method implemented\n'.format(self.name))
