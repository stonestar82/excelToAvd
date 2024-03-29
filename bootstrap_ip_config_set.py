#!/usr/bin/env python
#
# Copyright (c) 2015, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  - Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#  - Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#  - Neither the name of Arista Networks nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Bootstrap script
#
#    Written by:
#       EOS+, Arista Networks

# pylint: disable=W0703

import argparse
import datetime
import imp
import json
import jsonrpclib
import logging
import os
import os.path
import re
import sleekxmpp
import shutil
import socket
import subprocess
import sys
import time
import pwd
import grp
import crypt
import traceback
import urllib2
import urlparse

from collections import namedtuple
from logging.handlers import SysLogHandler
from string import Template              # pylint: disable=W0402
from subprocess import PIPE
from urlparse import urlsplit, urlunsplit
from operator import ne, eq
from EapiClientLib import EapiClient

# Server will replace this value with the correct IP address/hostname
# before responding to the bootstrap request.
SERVER = 'http://192.168.22.251'

LOGGING_FACILITY = 'ztpbootstrap'
SYSLOG = '/dev/log'
DEFAULT_SYSLOG_PORT = 514

CONTENT_TYPE_PYTHON = 'text/x-python'
CONTENT_TYPE_HTML = 'text/html'
CONTENT_TYPE_OTHER = 'text/plain'
CONTENT_TYPE_JSON = 'application/json'

TEMP = '/tmp'

COMMAND_API_SERVER = 'localhost'
COMMAND_API_USERNAME = 'ztps'
COMMAND_API_PASSWORD = 'ztps-password'
COMMAND_API_PROTOCOL = 'unix-socket'

HTTP_STATUS_OK = 200
HTTP_STATUS_CREATED = 201
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_CONFLICT = 409
HTTP_STATUS_INTERNAL_SERVER_ERROR = 500

FLASH = '/mnt/flash'

STARTUP_CONFIG = '%s/startup-config' % FLASH
RC_EOS = '%s/rc.eos' % FLASH

BOOT_EXTENSIONS = '%s/boot-extensions' % FLASH
BOOT_EXTENSIONS_FOLDER = '%s/.extensions' % FLASH

HTTP_TIMEOUT = 30

FLASH_FILES = []
RESTORE_FACTORY_FLASH = True

# pylint: disable=C0103
syslog_manager = None
xmpp_client = None
# pylint: enable=C0103

# --------------------------------XMPP------------------------
# Uncomment this section in order to enable XMPP debug logging
# logging.basicConfig(level=logging.DEBUG,
#                     format='%(levelname)-8s %(message)s')

# You will also have to comment out the following lines:
for logger in ['sleekxmpp.xmlstream.xmlstream',
               'sleekxmpp.basexmpp']:
    xmpp_log = logging.getLogger(logger)
    xmpp_log.addHandler(logging.NullHandler())
# --------------------------------XMPP------------------------

# --------------------------------SYSLOG----------------------
# Comment out this section in order to enable syslog debug
# logging
logging.raiseExceptions = False
# --------------------------------XMPP------------------------


# ------------------Utilities---------------------------------
def _exit(code):
    # pylint: disable=W0702

    # Wait for XMPP messages to drain
    time.sleep(3)

    if xmpp_client:
        try:
            xmpp_client.abort()
        except:
            pass

    if not RESTORE_FACTORY_FLASH:
        for path in [STARTUP_CONFIG, RC_EOS, BOOT_EXTENSIONS]:
            filename = path.split('/')[-1]
            if os.path.isfile(path):
                dst = '%s.ztp' % path
                log('Saving %s as %s...' % (filename, dst))

                if os.path.isfile(dst):
                    os.remove(dst)

                shutil.move(path, dst)

            backup_path = url_path_join('/', TEMP,
                                        os.path.basename(filename))

            if os.path.isfile(backup_path):
                log('Recovering %s...' % path)
                shutil.move(backup_path, path)

        if os.path.isdir(BOOT_EXTENSIONS_FOLDER):
            dst = '%s.ztp' % BOOT_EXTENSIONS_FOLDER
            log('Saving %s as %s...' %
                (BOOT_EXTENSIONS_FOLDER.split('/')[-1],
                 dst))

            if os.path.isdir(dst):
                shutil.rmtree(dst)

            shutil.move(BOOT_EXTENSIONS_FOLDER,
                        '%s.ztp' % BOOT_EXTENSIONS_FOLDER)

        backup_path = url_path_join(
            '/', TEMP,
            os.path.basename(BOOT_EXTENSIONS_FOLDER))
        if os.path.isdir(backup_path):
            log('Recovering %s...' % BOOT_EXTENSIONS_FOLDER)
            shutil.move(backup_path, BOOT_EXTENSIONS_FOLDER)
    else:
        if code:
            for path in [x for x in all_files_and_dirs(FLASH)
                         if x not in FLASH_FILES]:
                log('Deleting %s...' % path)
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    try:
                        os.remove(path)
                    except OSError:
                        # already removed
                        pass

    sys.stdout.flush()
    sys.stderr.flush()

    # pylint: disable=W0212
    # Need to close background sleekxmpp threads as well
    os._exit(code)

SYSTEM_ID = None
XMPP_MSG_TYPE = None


def log_xmpp():
    return XMPP_MSG_TYPE == 'debug'


def log(msg, error=False, xmpp=None):
    if xmpp is None:
        xmpp = log_xmpp()

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
    xmpp_msg = '%s: %s - %s%s' % (SYSTEM_ID if SYSTEM_ID else 'N/A',
                                  timestamp,
                                  'ERROR: ' if error else '',
                                  msg)

    if xmpp and xmpp_client and xmpp_client.connected:
        xmpp_client.message(xmpp_msg)

    if SYSTEM_ID:
        syslog_msg = '%s: %s' % (SYSTEM_ID, msg)
    else:
        syslog_msg = msg

    if error:
        print 'ERROR: %s' % syslog_msg
    else:
        print syslog_msg

    if syslog_manager:
        if error:
            syslog_manager.log.error(syslog_msg)
        else:
            syslog_manager.log.info(syslog_msg)


def url_path_join(*parts):
    """Normalize URL parts and join them with a slash."""
    # pylint: disable=W0142
    schemes, netlocs, paths, queries, fragments = \
        zip(*(urlsplit(part) for part in parts))
    scheme = get_first_token(schemes)
    netloc = get_first_token(netlocs)
    path = '/'.join(x.strip('/') for x in paths if x)
    query = get_first_token(queries)
    fragment = get_first_token(fragments)
    return urlunsplit((scheme, netloc, path, query, fragment))

# pylint: disable=C0103
_ntuple_diskusage = namedtuple('usage', 'total used free')
# pylint: enable=C0103


def flash_usage():
    stats = os.statvfs(FLASH)
    free = stats.f_bavail * stats.f_frsize
    total = stats.f_blocks * stats.f_frsize
    used = (stats.f_blocks - stats.f_bfree) * stats.f_frsize
    return _ntuple_diskusage(total, used, free)


def flash_snapshot():
    # pylint: disable=W0603
    global FLASH_FILES
    FLASH_FILES = all_files_and_dirs(FLASH)

    for filename in [STARTUP_CONFIG, RC_EOS, BOOT_EXTENSIONS]:
        if os.path.isfile(filename):
            log('Backing up %s...' % filename)

            # Delete old folder in tmp
            dst = url_path_join('/', TEMP,
                                os.path.basename(filename))
            if os.path.isfile(dst):
                os.remove(dst)

            shutil.move(filename, TEMP)

    if os.path.isdir(BOOT_EXTENSIONS_FOLDER):
        log('Backing up %s...' % BOOT_EXTENSIONS_FOLDER)

        # Delete old folder in /tmp
        dst = url_path_join('/', TEMP,
                            os.path.basename(BOOT_EXTENSIONS_FOLDER))
        if os.path.isdir(dst):
            shutil.rmtree(dst)

        shutil.move(BOOT_EXTENSIONS_FOLDER, TEMP)


def get_first_token(sequence):
    return next((x for x in sequence if x), '')


def all_files_and_dirs(path):
    result = []
    for top, dirs, files in os.walk(path):
        result += [os.path.join(top, d) for d in dirs]
        result += [os.path.join(top, f) for f in files]

    return result
# ------------------Utilities---------------------------------


# ------------------4.12.x support----------------------------
def download_file(url, path):
    if not urlparse.urlsplit(url).scheme:      # pylint: disable=E1103
        url = url_path_join(SERVER, url)

    log('Retrieving URL: %s' % url)

    url = urllib2.urlopen(url, timeout=HTTP_TIMEOUT)
    output_file = open(path, 'wb')
    output_file.write(url.read())
    output_file.close()

# pylint: disable=C0103
REQUESTS = 'requests-2.3.0'
REQUESTS_URL = url_path_join(SERVER, '/files/lib/', REQUESTS+'.tar.gz')
try:
    import requests
except ImportError:
    requests_url = '%s/%s.tar.gz' % (TEMP, REQUESTS)
    download_file(REQUESTS_URL, requests_url)
    cmd = 'sudo tar -xzvf %s -C /tmp;' \
          'cd %s/%s;' \
          'sudo python setup.py build;' \
          'sudo python setup.py install' % \
          (requests_url, TEMP, REQUESTS)
    res = os.system(cmd)
    if res:
        log('%s returned %s' % (cmd, res), error=True)
        _exit(1)
    import requests
# pylint: enable=C0103
# ------------------4.12.x support----------------------------


class ZtpError(Exception):
    pass


class ZtpActionError(ZtpError):
    pass


class ZtpUnexpectedServerResponseError(ZtpError):
    pass


class Attributes(object):

    def __init__(self, local_attr=None, special_attr=None):
        self.local_attr = local_attr if local_attr else []
        self.special_attr = special_attr if special_attr else []

    def get(self, attr, default=None):
        if attr in self.local_attr:
            return self.local_attr[attr]
        elif attr in self.special_attr:
            return self.special_attr[attr]
        else:
            return default

    def copy(self):
        attrs = dict()
        if self.special_attr:
            attrs = self.special_attr.copy()
        if self.local_attr:
            attrs.update(self.local_attr)
        return attrs


class Node(object):
    # pylint: disable=R0201

    '''Node object which can be used by actions via:
           attributes.get('NODE')

    Attributes:
      client (jsonrpclib.Server): jsonrpclib connect to Command API engine
    '''

    def __init__(self, server):
        self.server_ = server

        url = Node._enable_api()

        self.client = jsonrpclib.Server(url)

        try:
            self.api_enable_cmds([])
        except socket.error:
            raise ZtpError('unable to enable eAPI')

        # Workaround for BUG89374
        try:
            self._disable_copp()
        except jsonrpclib.jsonrpc.ProtocolError as err:
            log('WARNING: unable to disable COPP: %s '
                '(platform/EOS version might not support this feature)' %
                err)

        global SYSTEM_ID                    # pylint: disable=W0603
        SYSTEM_ID = \
            self.api_enable_cmds(['show version'])[0]['serialNumber']

    @classmethod
    def _cli_enable_cmd(cls, cli_cmd):
        bash_cmd = ['FastCli', '-p', '15', '-A', '-c', cli_cmd]
        proc = subprocess.Popen(bash_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (out, err) = proc.communicate()
        return (proc.returncode, out, err)      # pylint: disable=E1101

    @classmethod
    def _cli_config_cmds(cls, cmds):
        cls._cli_enable_cmd('\n'.join(['configure'] + cmds))

    @classmethod
    def _enable_api(cls):
        create_user = ''
        # Don't use unix sockets in CI environment
        if os.environ.get('EAPI_TEST') is not None:
            COMMAND_API_PROTOCOL = 'http'
            create_user = 'username %s secret %s privilege 15' % (
                          COMMAND_API_USERNAME,
                          COMMAND_API_PASSWORD)
            url = '%s://%s:%s@%s/command-api' % (COMMAND_API_PROTOCOL,
                                                 COMMAND_API_USERNAME,
                                                 COMMAND_API_PASSWORD,
                                                 COMMAND_API_SERVER)
        else:
            url = 'unix:/var/run/command-api.sock'
            _, out, _ = cls._cli_enable_cmd('show version | include image')
            version = out.split(': ')[1]
            (major, minor, patch) = version.split('.')[0:3]
            patch = int(list(filter(str.isdigit, patch))[0])
            if (int(major) <= 4 and int(minor) <= 14 and patch <= 5):
                COMMAND_API_PROTOCOL = 'http'
                create_user = 'username %s secret %s privilege 15' % (
                              COMMAND_API_USERNAME,
                              COMMAND_API_PASSWORD)
                url = '%s://%s:%s@%s/command-api' % (COMMAND_API_PROTOCOL,
                                                     COMMAND_API_USERNAME,
                                                     COMMAND_API_PASSWORD,
                                                     COMMAND_API_SERVER)
            else:
                COMMAND_API_PROTOCOL = 'unix-socket'

        cls._cli_config_cmds([create_user,
                              'management api http-commands',
                              'no protocol https',
                              'protocol %s' % COMMAND_API_PROTOCOL,
                              'no shutdown'])

        _, out, _ = cls._cli_enable_cmd('show management api http-commands |'
                                        ' grep running')
        retries = 3
        while not out and retries:
            log('Waiting for CommandAPI to be enabled...')
            time.sleep(1)
            retries = retries - 1
            _, out, _ = cls._cli_enable_cmd(
                'show management api http-commands | grep running')
        return url

    def _disable_copp(self):
        # COPP does not apply to vEOS or EOS-4.11.x and earlier
        if (self.system()['model'] != 'vEOS' and
            len(self.system()['version'].split('.')) > 2 and
            int(self.system()['version'].split('.')[1]) < 12):
            self.api_config_cmds([
                'control-plane',
                'no service-policy input copp-system-policy'])

    def _has_rc_eos(self):
        return os.path.isfile(RC_EOS)

    def _append_lines(self, filename, lines):
        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            fileexists = True
        else:
            fileexists = False

        with open(filename, 'a') as output:
            if fileexists:
                output.write('\n')
            output.write('\n'.join(lines))

    @classmethod
    def bash_cmds(cls, cmds):
        '''Executes bash commands in order - stops on first failure.

        Args:
            cmds: list of bash commands

        Returns:
            cmd:  first failing command (None otherwise)
            code: exit code for first failing command (None otherwise)
            out:  stdout for first failing command (None otherwise)
            err:  stderr for first failing command (None otherwise)
        '''

        for bash_cmd in cmds:
            proc = subprocess.Popen(bash_cmd, stdin=PIPE,
                                    stdout=PIPE, stderr=PIPE,
                                    shell=True)
            code = proc.returncode         # pylint: disable=E1101
            (out, err) = proc.communicate()
            if code or err:
                return (bash_cmd, code, out, err)
            else:
                print out

        return (None, None, None, None)

    @classmethod
    def substitute(cls, template, substitutions, strict=True):
        '''Perform variable substitution on a config template.

        Args:
            template (string): EOS configuration template
            substitutions (dict): set of substitutions for the template
            strict (bool, optional): If true, method will raise Exception
                                     when template variables are missing
                                     from 'substitutions'.

        Returns:
            string: template string with variable substitution
        '''
        try:
            if strict:
                return Template(template).substitute(substitutions)
            else:
                return Template(template).safe_substitute(substitutions)
        except KeyError as exc:
            raise Exception('Unable to perform variable substitution - '
                            '\'%s\' missing from list of substitutions' %
                            exc.message)

    def api_enable_cmds(self, cmds, text_format=False):
        '''Run CLI commands via Command API, starting from enable mode.

        Commands are ran in order.

        Args:
            cmds (list): List of CLI commands.
            text_format (bool, optional): If true, Command API request will run
                                          in text mode (instead of JSON).

        Returns:
            list: List of Command API results corresponding to the
                  input commands.
        '''
        req_format = 'text' if text_format else 'json'

        result = None
        try:
            result = self.client.runCmds(1, ['enable'] + cmds, req_format)
        except Exception as exc:
            # EOS-4.14.5+: persistent connection might be have been closed
            # on timeout - should recover on first retry
            if exc.args[0] == 32:      # Broken PIPE
                result = self.client.runCmds(1, ['enable'] + cmds, req_format)
            else:
                raise exc

        if text_format:
            return [x.values()[0] for x in result if x.values()][1:]
        else:
            return result[1:]

    def api_config_cmds(self, cmds):
        '''Run CLI commands via Command API, starting from config mode.

        Commands are ran in order.

        Args:
            cmds (list): List of CLI commands.

        Returns:
            list: List of Command API results corresponding to the
                  input commands.
        '''
        return self.api_enable_cmds(['configure'] + cmds)[1:]

    def system(self):
        '''Get system information.

        Returns:
            dict: System information

            Format::

                {'model':        <MODEL>,
                 'version':      <EOS_VERSION>,
                 'systemmac':    <SYSTEM_MAC>,
                 'serialnumber': <SERIAL_NUMBER>}

        '''

        result = {}
        info = self.api_enable_cmds(['show version'])[0]

        result['model'] = info['modelName']
        result['version'] = info['version']
        result['systemmac'] = info['systemMacAddress']
        result['serialnumber'] = info['serialNumber']

        return result

    def neighbors(self):
        '''Get neighbors.

        Returns:
            dict: LLDP neighbor

            Format::

                {'neighbors': {<LOCAL_PORT>:
                 [{'device': <REMOTE_DEVICE>,
                   'port': <REMOTE_PORT>}, ...],
                ...}}

        '''

        result = {}
        info = self.api_enable_cmds(['show lldp neighbors'])[0]
        result['neighbors'] = {}
        for entry in info['lldpNeighbors']:
            neighbor = {}
            neighbor['device'] = entry['neighborDevice']
            neighbor['port'] = entry['neighborPort']
            if entry['port'] in result['neighbors']:
                result['neighbors'][entry['port']] += [neighbor]
            else:
                result['neighbors'][entry['port']] = [neighbor]
        return result

    def details(self):
        '''Get details.

        Returns:
            dict: System details

            Format::

                {'model':        <MODEL>,
                 'version':      <EOS_VERSION>,
                 'systemmac':    <SYSTEM_MAC>,
                 'serialnumber': <SERIAL_NUMBER>,
                 'neighbors':    <NEIGHBORS>        # see neighbors()
                }

        '''

        return dict(self.system().items() +
                    self.neighbors().items())

    def has_startup_config(self):
        '''Check whether startup-config is configured or not.

        Returns:
            bool: True is startup-config is configured; false otherwise.
        '''
        return os.path.isfile(STARTUP_CONFIG) and \
               open(STARTUP_CONFIG).read().strip()

    def append_startup_config_lines(self, lines):
        '''Add lines to startup-config.

        Args:
            lines (list): List of CLI commands
        '''
        self._append_lines(STARTUP_CONFIG, lines)

    def append_rc_eos_lines(self, lines):
        '''Add lines to rc.eos.

        Args:
            lines (list): List of bash commands
        '''
        if not self._has_rc_eos():
            lines = ['#!/bin/bash'] + lines
        self._append_lines(RC_EOS, lines)

    def log_msg(self, msg, error=False):
        '''Log message via configured syslog/XMPP.

        Args:
            msg (string): Message
            error (bool, optional): True if msg is an error; false otherwise.
        '''
        log(msg, error)

    def rc_eos(self):
        '''Get rc.eos path.

        Returns:
            string: rc.eos path
        '''
        return RC_EOS

    def flash(self):
        '''Get flash path.

        Returns:
            string: flash path
        '''
        return FLASH

    def startup_config(self):
        '''Get startup-config path.

        Returns:
            string: startup-config path
        '''
        return STARTUP_CONFIG

    def retrieve_url(self, url, path):
        '''Download resource from server.

        If 'path' is somewhere on flash and 'url' points back to
        SERVER, then the client will request the metadata for
        the resource from the server (in order to check whether there
        is enough disk space available). If 'url' points to a different
        server, then the 'content-length' header will be used for the
        disk space checks.

        Raises:
            ZtpError: resource cannot be retrieved:
                - metadata cannot be retrieved from server OR
                - metadata is inconsistent with request OR
                - disk space on flash is insufficient OR
                - file cannot be written to disk

        Returns:
            string: startup-config path
        '''
        self.server_.get_resource(url, path)

    def create_user(self, user, group, passwd, root='/persist/local/',
                    ssh_keys=None):

        '''Create a local user on the bootstrapped node. If 'ssh_keys' are
        provided, they will be copied to $HOME/.ssh/authorized_keys. Also,
        rc.eos will be modified to add this user on every boot. If the user
        provided already exists, the function will continue and install the
        ssh_keys (if necessary). The $HOME/.ssh directory will be assigned
        0700 permissions and the $HOME/.ssh/authorized_keys file will be
        assigned 0600 permissions in accord with SSH best practices.

        Args:
         - user: the username
         - group: the group assigned to the user
         - passwd: cleartext password
         - root: the path where the user's home directory will reside
         - ssh_keys: (optional) public keys that will be copied to
           ~$HOME/.ssh/authorized_keys

        Raises:
            ZtpError
            - missing argument: user, group, passwd
            - useradd fails, return the error
            - ssh_keys cannot be written to 'authorized_keys'
            - files cannot change ownership or permissions

        Returns:
            bool: True if user created; False if otherwise
        '''
        if not user:
            raise ZtpError('A user must be provided for create_user()')

        if not group:
            raise ZtpError('A group must be provided for create_user()')

        if not passwd:
            raise ZtpError('A passwd must be provided for create_user()')

        if not root:
            root = '/persist/local/'

        home = os.path.join(root, user)
        ssh_path = os.path.join(home, '.ssh')
        auth_path = os.path.join(ssh_path, 'authorized_keys')

        # Encrypt password
        enc_passwd = crypt.crypt(passwd, "22")

        add_cmd = 'sudo useradd -p %s -d %s -G %s %s' % (enc_passwd, home,
                                                         group, user)

        # Create user
        try:
            proc = subprocess.Popen(add_cmd, stdin=PIPE, stdout=PIPE,
                                    stderr=PIPE, shell=True)

            (_, err) = proc.communicate()
            return_code = proc.wait()       # pylint: disable=E1101

            if return_code or err:
                if return_code in (4, 9):
                    self.log_msg('User already exists - continuing. (%s:%s)'
                                 % (return_code, err))
                else:
                    raise ZtpError('Failed to add user.(%s:%s)'
                                   % (return_code, err))

        except Exception as exc:
            raise ZtpError(exc)

        # Get User ID and Group ID for chown
        uid = pwd.getpwnam(user).pw_uid
        gid = grp.getgrnam(group).gr_gid

        # Write keys if provided
        if ssh_keys:

            if not os.path.exists(home):
                os.mkdir(ssh_path, 0700)

            if not os.path.exists(ssh_path):
                os.mkdir(ssh_path, 0700)
            else:
                os.chmod(ssh_path, 0700)

            os.chown(ssh_path, uid, gid)

            auth_keys = open(auth_path, 'ab+')
            auth_keys.write(ssh_keys)
            auth_keys.close()
            os.chown(auth_path, uid, gid)
            os.chmod(auth_path, 0600)

        self.append_rc_eos_lines([add_cmd])

        return

    @classmethod
    def server_address(cls):
        '''Get ZTP Server URL.

        Returns:
            string: ZTP Server URL.
        '''
        return SERVER


class SyslogManager(object):

    def __init__(self):
        self.log = logging.getLogger('ztpbootstrap')
        self.log.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter('ZTPS - %(levelname)s: '
                                           '%(message)s')

        # syslog to localhost enabled by default
        self._add_syslog_handler()

    def _add_handler(self, handler, level=None):
        if level is None:
            level = 'DEBUG'

        try:
            handler.setLevel(logging.getLevelName(level))
        except ValueError:
            log('SyslogManager: unknown logging level (%s) - using '
                'log.DEFAULT instead' % level, error=True)
            handler.setLevel(logging.DEBUG)

        handler.setFormatter(self.formatter)
        self.log.addHandler(handler)

    def _add_syslog_handler(self):
        log('SyslogManager: adding localhost handler')
        self._add_handler(SysLogHandler(address=SYSLOG))

    def _add_file_handler(self, filename, level=None):
        log('SyslogManager: adding file handler (%s - level:%s)' %
            (filename, level))
        self._add_handler(logging.FileHandler(filename), level)

    def _add_remote_syslog_handler(self, host, port, level=None):
        log('SyslogManager: adding remote handler (%s:%s - level:%s)' %
            (host, port, level))
        self._add_handler(SysLogHandler(address=(host, port)), level)

    def add_handlers(self, handler_config):
        for entry in handler_config:
            match = re.match('^file:(.+)',
                             entry['destination'])
            if match:
                self._add_file_handler(match.groups()[0],
                                       entry['level'])
            else:
                match = re.match('^(.+):(.+)',
                                 entry['destination'])
                if match:
                    self._add_remote_syslog_handler(match.groups()[0],
                                                    int(match.groups()[1]),
                                                    entry['level'])
                else:
                    self._add_remote_syslog_handler(entry['destination'],
                                                    DEFAULT_SYSLOG_PORT,
                                                    entry['level'])


class Server(object):

    def __init__(self):
        pass

    @classmethod
    def _http_request(cls, path=None, method='get', headers=None,
                      payload=None, files=None, local_file=None):
        if headers is None:
            headers = {}
        # Disable gzip, deflate so we can safely determine available space
        headers[u'Accept-Encoding'] = None
        if files is None:
            files = []

        request_files = []
        for entry in files:
            request_files[entry] = open(entry, 'rb')

        if not urlparse.urlsplit(path).scheme:   # pylint: disable=E1103
            full_url = url_path_join(SERVER, path)
        else:
            full_url = path

        response = None
        try:
            if method == 'get':
                log('GET %s' % full_url)
                response = requests.get(full_url,
                                        data=json.dumps(payload),
                                        headers=headers,
                                        files=request_files,
                                        timeout=HTTP_TIMEOUT)
            elif method == 'post':
                log('POST %s' % full_url)
                response = requests.post(full_url,
                                         data=json.dumps(payload),
                                         headers=headers,
                                         files=request_files,
                                         timeout=HTTP_TIMEOUT)
            elif method == 'stream':
                log('STREAM %s - %s' % (full_url, local_file))
                # Don't use streaming request in CI environment
                if os.environ.get('EAPI_TEST') is not None:
                    log('NOT STREAM FOR CI %s - %s' % (full_url, local_file))
                    response = requests.get(full_url,
                                            data=json.dumps(payload),
                                            headers=headers,
                                            files=request_files,
                                            timeout=HTTP_TIMEOUT)
                else:
                    if not local_file:
                        raise ZtpError('Cant STREAM EOS image file without'
                                       ' file name and path')
                    with requests.get(full_url, stream=True) as response:
                        response.raise_for_status()
                        with open(local_file, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
            else:
                log('Unknown method %s' % method, error=True)
        except requests.exceptions.ConnectionError:
            raise ZtpError('server connection error')

        return response

    def _get_request(self, url, stream=False, local_file=None):
        # resource or action
        headers = {'content-type': CONTENT_TYPE_HTML}
        if stream:
            result = self._http_request(url, method='stream', headers=headers,
                                        local_file=local_file)
        else:
            result = self._http_request(url, headers=headers)
        log('Server response to GET request: status=%s' % result.status_code)

        return (result.status_code,
                result.headers['content-type'].split(';')[0],
                result)

    def _save_file_contents(self, contents, path, url=None):
        if path.startswith(FLASH):
            if not url:
                raise ZtpError('attempting to save file to %s, but cannot'
                               'retrieve content metadata' % path)

            size = 0
            if 'content-length' in contents.headers:
                size = int(contents.headers['content-length'])

            if url.startswith(SERVER):
                _, _, metadata = self.get_metadata(url)
                metadata = metadata.json()
                if size and metadata['size'] != size:
                    raise ZtpError('"content-length" for %s does not match '
                                   'metadata: %s != %s' %
                                   (url, metadata['size'], size))

            usage = flash_usage()

            free_space = usage.free
            potential_used_space = size + usage.used
            if os.path.isfile(path):
                size = os.path.getsize(path)
                free_space += size
                potential_used_space -= size

            if (size > free_space):
                raise ZtpError('not enough memory on flash for saving %s to %s'
                               ' (free: %s bytes, required: %s bytes)' %
                               (url, path, free_space, size))
            elif (potential_used_space > 0.9 * usage.total):
                percent = (size + usage.used) * 100.0 / usage.total
                log('WARNING: flash disk usage will exceeed %s%% after '
                    'saving %s to %s' % (percent, url, path))

            log('File streamed earlier. No need to write content.')

        write_response_contents = False
        if os.environ.get('EAPI_TEST') is not None:
            log('File not streamed earlier in CI environment. Need to write content')
            write_response_contents = True

        if not path.startswith(FLASH) or write_response_contents:
            log('Writing %s...' % path)
            # Save contents to file
            try:
                with open(path, 'wb') as result:
                    for chunk in contents.iter_content(chunk_size=1024):
                        if chunk:
                            result.write(chunk)
                    result.close()
            except IOError as err:
                raise ZtpError('unable to write %s: %s' % (path, err))

        # Set permissions
        os.chmod(path, 0777)

    def get_config(self):
        headers = {'content-type': CONTENT_TYPE_HTML}
        result = self._http_request('bootstrap/config',
                                    headers=headers)

        log('Server response to GET config: contents=%s' % result.json())

        status = result.status_code
        content = result.headers['content-type'].split(';')[0]
        if(status != HTTP_STATUS_OK or
           content != CONTENT_TYPE_JSON):
            raise ZtpUnexpectedServerResponseError(
                'unexpected response from server (status=%s; content-type=%s)' %
                (status, content))

        return (status, content, result)

    def post_nodes(self, node):
        headers = {'content-type': CONTENT_TYPE_JSON}
        result = self._http_request('nodes',
                                    method='post',
                                    headers=headers,
                                    payload=node)
        location = result.headers['location'] \
            if 'location' in result.headers \
            else None
        log('Server response to POST nodes: status=%s, location=%s' %
            (result.status_code, location))

        status = result.status_code
        content = result.headers['content-type'].split(';')[0]
        if(status not in [HTTP_STATUS_CREATED,
                          HTTP_STATUS_BAD_REQUEST,
                          HTTP_STATUS_CONFLICT] or
           content != CONTENT_TYPE_HTML):
            raise ZtpUnexpectedServerResponseError(
                'unexpected response from server (status=%s; content-type=%s)' %
                (status, content))
        elif status == HTTP_STATUS_BAD_REQUEST:
            raise ZtpError('node not found on server (status=%s)' % status)

        return (status, content, location)

    def get_definition(self, location):
        headers = {'content-type': CONTENT_TYPE_HTML}
        result = self._http_request(location,
                                    headers=headers)

        if result.status_code == HTTP_STATUS_OK:
            log('Server response to GET definition: status=%s, contents=%s' %
                (result.status_code, result.json()))
        else:
            log('Server response to GET definition: status=%s' %
                result.status_code)

        status = result.status_code
        content = result.headers['content-type'].split(';')[0]
        if not ((status == HTTP_STATUS_OK and
                 content == CONTENT_TYPE_JSON) or
                (status == HTTP_STATUS_BAD_REQUEST and
                 content == CONTENT_TYPE_HTML)):
            raise ZtpUnexpectedServerResponseError(
                'unexpected response from server (status=%s; content-type=%s)' %
                (status, content))
        elif status == HTTP_STATUS_BAD_REQUEST:
            raise ZtpError('server-side topology check failed (status=%s)' %
                           status)

        return (status, content, result)

    def get_action(self, action):
        status, content, action_response = \
            self._get_request('actions/%s' % action)

        if not ((status == HTTP_STATUS_OK and
                 content == CONTENT_TYPE_PYTHON) or
                (status == HTTP_STATUS_NOT_FOUND and
                 content == CONTENT_TYPE_HTML)):
            raise ZtpUnexpectedServerResponseError(
                'unexpected response from server (status=%s; content-type=%s)' %
                (status, content))
        elif status == HTTP_STATUS_NOT_FOUND:
            raise ZtpError('action not found on server (status=%s)' % status)

        filename = os.path.join(TEMP, action)
        self._save_file_contents(action_response, filename)
        return filename

    def get_metadata(self, url):
        if urlparse.urlsplit(url).scheme:   # pylint: disable=E1103
            regex = re.compile(SERVER, re.IGNORECASE)
            if regex.match(url):
                url = re.sub(regex, '', url)
                url = url_path_join(SERVER, '/meta', url)
        else:
            aux = [x for x in url.split('/') if x]
            url = '/'.join(['meta'] + aux)

        headers = {'content-type': CONTENT_TYPE_HTML}
        result = self._http_request(url,
                                    headers=headers)
        log('Server response to GET meta: contents=%s' % result.json())

        status = result.status_code
        content = result.headers['content-type'].split(';')[0]

        if not ((status == HTTP_STATUS_OK and
                 content == CONTENT_TYPE_JSON) or
                (status == HTTP_STATUS_NOT_FOUND and
                 content == CONTENT_TYPE_HTML) or
                (status == HTTP_STATUS_INTERNAL_SERVER_ERROR and
                 content == CONTENT_TYPE_HTML)):
            raise ZtpUnexpectedServerResponseError(
                'unexpected response from server (status=%s; content-type=%s)' %
                (status, content))
        elif status == HTTP_STATUS_NOT_FOUND:
            raise ZtpError('metadata not found on server (status=%s)' %
                           status)
        elif status == HTTP_STATUS_INTERNAL_SERVER_ERROR:
            raise ZtpError(
                'unable to retrieve metadata from server (status=%s)' %
                status)

        return (status, content, result)

    def get_resource(self, url, path):
        if not urlparse.urlsplit(url).scheme:     # pylint: disable=E1103
            url = url_path_join(SERVER, url)

        if path.startswith(FLASH):
            status, content, response = self._get_request(url, stream=True,
                                                          local_file=path)
        else:
            status, content, response = self._get_request(url)

        if url.startswith(SERVER):
            if not ((status == HTTP_STATUS_OK and
                     content == CONTENT_TYPE_OTHER) or
                    (status == HTTP_STATUS_NOT_FOUND and
                     content == CONTENT_TYPE_HTML)):
                raise ZtpUnexpectedServerResponseError(
                    'unexpected response from server for %s '
                    '(status=%s; content-type=%s)' %
                    (url, status, content))
        else:
            if not (status == HTTP_STATUS_OK or
                    status == HTTP_STATUS_NOT_FOUND):
                raise ZtpUnexpectedServerResponseError(
                    'unexpected response from server for %s '
                    '(status=%s; content-type=%s)' %
                    (url, status, content))

        if status == HTTP_STATUS_NOT_FOUND:
            raise ZtpError('resource %s not found on server (status=%s)' %
                           (url, status))

        self._save_file_contents(response, path, url)


class XmppClient(sleekxmpp.ClientXMPP):
    # pylint: disable=W0613, R0904, R0201, R0924

    def __init__(self, user, domain, password, rooms,
                 nick, xmpp_server, xmpp_port):

        self.xmpp_jid = '%s@%s' % (user, domain)
        self.connected = False

        try:
            sleekxmpp.ClientXMPP.__init__(self, self.xmpp_jid,
                                          password)
        except sleekxmpp.jid.InvalidJID:
            log('Unable to connect XMPP client because of invalid jid: %s' %
                self.xmpp_jid, xmpp=False)
            return

        self.xmpp_nick = nick
        self.xmpp_rooms = rooms

        self.xmpp_rooms = []
        for room in rooms:
            self.xmpp_rooms.append('%s@conference.%s' % (room, domain))

        self.add_event_handler('session_start', self._session_connected)
        self.add_event_handler('connect', self._session_connected)
        self.add_event_handler('disconnected', self._session_disconnected)

        # Multi-User Chat
        self.register_plugin('xep_0045')
        # XMPP Ping
        self.register_plugin('xep_0199')
        # Service Discovery
        self.register_plugin('xep_0030')

        log('XmppClient connecting to server...', xmpp=False)
        if xmpp_server is not None:
            self.connect((xmpp_server, xmpp_port), reattempt=False)
        else:
            self.connect(reattempt=False)

        self.process(block=False)

        retries = 3
        while not self.connected and retries:
            # Wait to connect
            time.sleep(1)
            retries -= 1

    def _session_connected(self, event):
        log('XmppClient: Session connected (%s)' % self.xmpp_jid,
            xmpp=False)
        self.send_presence()
        self.get_roster()

        self.connected = True

        # Joining rooms
        for room in self.xmpp_rooms:
            self.plugin['xep_0045'].joinMUC(room,
                                            self.xmpp_nick,
                                            wait=True)
            log('XmppClient: Joined room %s as %s' %
                (room, self.xmpp_nick),
                xmpp=False)

    def _session_disconnected(self, event):
        log('XmppClient: Session disconnected (%s)' % self.xmpp_jid,
            xmpp=False)
        self.connected = False

    def message(self, message):
        for room in self.xmpp_rooms:
            self.send_message(mto=room,
                              mbody=message,
                              mtype='groupchat')


def apply_config(config, node):
    global xmpp_client                      # pylint: disable=W0603

    log('Applying server config')

    # XMPP not configured yet
    xmpp_config = config.get('xmpp', {})

    global XMPP_MSG_TYPE                        # pylint: disable=W0603
    XMPP_MSG_TYPE = xmpp_config.get('msg_type', 'debug')
    if XMPP_MSG_TYPE not in ['debug', 'info']:
        log('XMPP configuration failed because of unexpected \'msg_type\': '
            '%s not in [\'debug\', \'info\']' % XMPP_MSG_TYPE, error=True,
            xmpp=False)
    else:
        if xmpp_config:
            log('Configuring XMPP', xmpp=False)
            if ('username' in xmpp_config and
                'domain' in xmpp_config and
                'password' in xmpp_config and
                'rooms' in xmpp_config and
                xmpp_config['rooms']):
                nick = node.system()['serialnumber']
                if not nick:
                    # vEOS might not have a serial number configured
                    nick = node.system()['systemmac']
                xmpp_client = XmppClient(xmpp_config['username'],
                                         xmpp_config['domain'],
                                         xmpp_config['password'],
                                         xmpp_config['rooms'],
                                         nick,
                                         xmpp_config.get('server', None),
                                         xmpp_config.get('port', 5222))
            else:
                # XMPP not configured yet
                log('XMPP configuration failed because server response '
                    'is missing config details',
                    error=True, xmpp=False)
        else:
            log('No XMPP configuration received from server', xmpp=False)

    log_config = config.get('logging', [])
    if log_config:
        log('Configuring syslog')
        syslog_manager.add_handlers(log_config)
    else:
        log('No XMPP configuration received from server')


def execute_action(server, action_details, special_attr):
    action = action_details['action']

    description = ''
    if 'description'in action_details:
        description = '(%s)' % action_details['description']

    if action not in sys.modules:
        log('Downloading action %s%s' % (action, description))
        filename = server.get_action(action)

    log('Executing action %s' % action)
    if 'onstart' in action_details:
        log('Action %s: %s' % (action, action_details['onstart']),
            xmpp=True)

    try:
        if action in sys.modules:
            module = sys.modules[action]
        else:
            module = imp.load_source(action, filename)

        local_attr = action_details['attributes'] \
                     if 'attributes' in action_details \
                     else []
        try:
            module.main(Attributes(local_attr, special_attr))
        except Exception as exc:
            raise ZtpActionError(exc)
        log('Action executed succesfully (%s)' % action)
        if 'onsuccess' in action_details:
            log('Action %s: %s' % (action, action_details['onsuccess']),
                xmpp=True)
    except Exception as err:                  # pylint: disable=W0703
        if 'onfailure' in action_details:
            log('Action %s: %s' % (action, action_details['onfailure']),
                xmpp=True)
        raise ZtpActionError('executing action failed (%s): %s' % (action,
                                                                   err))


def main():
    # pylint: disable=W0603,R0912,R0915
    global syslog_manager, RESTORE_FACTORY_FLASH  

    cli_cmd = [
                "username ansible secret ansible privilege 15",
                "logging buffered 1000",
                "logging console informational",
                "logging monitor informational",
                "logging synchronous level all"
            ]

    cli_cmd = '\n'.join(['configure'] + cli_cmd)

    print(cli_cmd)

    bash_cmd = ['FastCli', '-p', '15', '-A', '-c', cli_cmd]
    proc = subprocess.Popen(bash_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    proc.communicate()

if __name__ == '__main__':
    try:
        main()
    except ZtpError as exception:
        log('Bootstrap process failed: %s' % str(exception), error=True)
        _exit(1)
    except KeyboardInterrupt:
        log('Bootstrap process keyboard-interrupted', error=True)
        log(sys.exc_info()[0])
        log(traceback.format_exc())
        _exit(1)
    except Exception, exception:
        errStr = 'Bootstrap process failed because of unknown' \
                 ' exception: %s' % exception
        log(errStr, error=True)
        log(sys.exc_info()[0])
        log(traceback.format_exc())
        _exit(1)



