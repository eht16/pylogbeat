# -*- coding: utf-8 -*-

from datetime import datetime
from json import dumps
import logging
import os

from pylogbeat import PyLogBeatClient


logging.basicConfig(level=logging.DEBUG)
logging.getLogger('pylogbeat').setLevel(logging.DEBUG)


HOST = 'localhost'
PORT = 61004
MESSAGE = {
    "@timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
    "@version": "1",
    "host": "my-local-host",
    "level": "INFO",
    "logsource": "my-local-host",
    "message": "foo bar",
    "pid": os.getpid(),
    "program": "example.py",
    "type": "python-logstash"
}
SSL_VERIFY = True
KEYFILE = 'certificate.key'
CERTFILE = 'certificate.crt'
CA_CERTS = 'ca.crt'


def main():
    client_arguments = dict(
        host=HOST,
        port=PORT,
        ssl_enable=True,
        ssl_verify=SSL_VERIFY,
        keyfile=KEYFILE,
        certfile=CERTFILE,
        ca_certs=CA_CERTS,
        use_logging=True)

    client = PyLogBeatClient(**client_arguments)
    client.connect()

    message = MESSAGE

    # send a single message, as dictionary
    client.send([message] * 2)
    client.close()

    with PyLogBeatClient(**client_arguments) as client_2:
        # send a single message, as JSON
        json_message = dumps(message)
        client_2.send([message])

        # send multiple messages
        client_2.send([json_message, message, json_message, message])


if __name__ == '__main__':
    main()
