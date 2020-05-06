# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the Apache License, Version 2.0 license.  See the LICENSE file for details.


SOCKET_HOST = 'localhost'
SOCKET_PORT = 99999  # invalid port on purpose
SOCKET_TIMEOUT = 66
SSL_KEYFILE = 'keyfile'
SSL_CERTFILE = 'certfile'
SSL_CACERTS = 'ca_certs'

MESSAGE = {
    "@timestamp": "2018-12-04T01:01:27",
    "@version": "1",
    "host": "my-local-host",
    "level": "INFO",
    "logsource": "my-local-host",
    "message": "foo bar",
    "pid": 1234,
    "program": "example.py",
    "type": "python-logstash"
}

MESSAGE_JSON = '''
{
    "@timestamp": "2018-12-04T01:01:27",
    "@version": "1",
    "host": "my-local-host",
    "level": "INFO",
    "logsource": "my-local-host",
    "message": "foo bar",
    "pid": 1234,
    "program": "example.py",
    "type": "python-logstash"
}
'''
