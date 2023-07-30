# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the Apache License, Version 2.0 license.  See the LICENSE file for details.

"""
PyLogBeat is a simple, incomplete implementation of the Beats protocol
used by Elastic Beats and Logstash.
"""

from collections.abc import Mapping, Sequence, Set
from datetime import datetime
from struct import pack, unpack
import json
import logging
import socket
import ssl
import sys
import zlib


__version__ = '2.0.1'

FRAME_TYPE_ACK = 0x41               # 'A'
FRAME_TYPE_COMPRESSED_FRAME = 0x43  # 'C'
FRAME_TYPE_JSON_FRAME = 0x4A        # 'J'
FRAME_TYPE_WINDOW_SIZE = 0x57       # 'W'
PAYLOAD_CHARSET = 'utf-8'           # encoding used for the payload / input message
PROTOCOL_VERSION = 0x32             # version = 2
SEQUENCE_MAX = 0x3FFFFFFFFFFFFFFF   #
TIMEOUT = 60

LOGGER = logging.getLogger('pylogbeat')
LOGGER.setLevel(logging.WARNING)   # disable log messages by default


class ConnectionException(Exception):
    pass


class PyLogBeatClient(object):  # pylint: disable=bad-option-value,useless-object-inheritance

    def __init__(  # pylint: disable=too-many-arguments
            self,
            host,
            port,
            timeout=None,
            ssl_enable=False,
            ssl_verify=True,
            keyfile=None,
            certfile=None,
            ca_certs=None,
            use_logging=False):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._ssl_enable = ssl_enable
        self._ssl_verify = ssl_verify
        self._keyfile = keyfile
        self._certfile = certfile
        self._ca_certs = ca_certs
        self._socket = None
        self._window_size = 0
        self._sequence = 0
        self._last_ack = 0
        self._use_logging = use_logging

    def _log(self, level, format_, *args, **kwargs):
        if self._use_logging:
            LOGGER.log(level, format_, *args, **kwargs)
        elif level >= logging.WARNING:  # print warnings to stderr
            message = format_.format(*args, **kwargs)
            message_format = f'{datetime.now()} {logging.getLevelName(level)} {message}'
            print(message_format, *args, file=sys.stderr, **kwargs)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type_, value, traceback):
        self.close()

    def connect(self):
        if self._socket is not None:
            return  # already connected

        self._create_and_connect_socket()

        if self._ssl_enable:
            self._setup_ssl_socket()

    def _create_and_connect_socket(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if self._timeout is not None:
            self._socket.settimeout(self._timeout)
        self._socket.connect((self._host, self._port))

    def _setup_ssl_socket(self):
        if self._ssl_verify:
            cert_reqs = ssl.CERT_REQUIRED
        elif self._ca_certs:
            cert_reqs = ssl.CERT_OPTIONAL
        else:
            cert_reqs = ssl.CERT_NONE

        ssl_context = ssl.create_default_context(cafile=self._ca_certs)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = cert_reqs
        if self._certfile and self._keyfile:
            ssl_context.load_cert_chain(self._certfile, self._keyfile)
        self._socket = ssl_context.wrap_socket(self._socket, server_side=False)

    def close(self):
        if self._socket is None:
            return  # nothing to do

        try:
            self._socket.close()
        except socket.error as exc:
            self._log(logging.ERROR, f'Error closing socket: {exc}', exc_info=True)
        finally:
            self._socket = None

    def send(self, elements):
        self._validate_elements_sequence(elements)

        self.connect()  # lazy init

        self._reinit_last_ack()

        self._window_size = self._factor_window_size(elements)
        payload = self._factor_payload(elements)
        compressed_payload = self._compress_payload(payload)

        self._send_window_size()
        self._send_payload(compressed_payload)

        while not self._expected_ack_received():
            self._read_ack()

    def _validate_elements_sequence(self, elements):
        # exclude strings to not detect them below as sequence
        valid_string_types = (str, bytes)
        if isinstance(elements, valid_string_types):
            raise TypeError(f'Passed value has type "{type(elements)}" but a sequence is expected')

        sequence_types = (Sequence, Set)
        if not isinstance(elements, sequence_types):
            raise TypeError(f'Passed value has type "{type(elements)}" but a sequence is expected')

        if not elements:
            return  # an empty sequence doesn't make much sense but is ok

        # check the elements to be a dict or string
        for element in elements:
            if isinstance(element, valid_string_types):
                continue
            if isinstance(element, Mapping):
                continue

            element_index = elements.index(element)
            raise TypeError(
                f'Element {element_index} has type "{type(element)}" but a mapping, '
                'bytes or string object is expected')

    def _reinit_last_ack(self):
        self._last_ack = 0

    def _factor_window_size(self, elements):
        return len(elements)

    def _factor_payload(self, elements):
        payload_elements = []
        for element in elements:
            self._increment_sequence()
            encoded_element = self._encode_json(element)
            payload_elements.append(encoded_element)

        return b''.join(payload_elements)

    def _increment_sequence(self):
        self._sequence += 1
        if self._sequence > SEQUENCE_MAX:
            self._sequence = 0

    def _encode_json(self, element):
        if isinstance(element, Mapping):
            element = json.dumps(element)

        if isinstance(element, str):
            element = element.encode(PAYLOAD_CHARSET)

        json_length = len(element)
        frame = [PROTOCOL_VERSION, FRAME_TYPE_JSON_FRAME, self._sequence, json_length, element]
        pack_param = f'>BBII{json_length}s'

        payload = pack(pack_param, *frame)
        return payload

    def _compress_payload(self, payload):
        compressed_payload = zlib.compress(payload)
        compressed_payload_bytes = len(compressed_payload)
        pack_format = f'>BBI{compressed_payload_bytes}s'
        compress = pack(
            pack_format,
            PROTOCOL_VERSION,
            FRAME_TYPE_COMPRESSED_FRAME,
            compressed_payload_bytes,
            compressed_payload)
        return compress

    def _send_window_size(self):
        packed_window_size = pack(
            '>BBI',
            PROTOCOL_VERSION,
            FRAME_TYPE_WINDOW_SIZE,
            self._window_size)
        self._socket.send(packed_window_size)
        self._log(logging.DEBUG, f'Sent window size: {self._window_size}')

    def _send_payload(self, compressed_payload):
        def chunker(chunk, size):
            for i in range(0, len(chunk), size):
                start = i
                end = start + size
                yield chunk[start:end]

        written_bytes = 0
        # SSL and TLS channels must be segmented into records of no more than 16Kb
        for segment in chunker(compressed_payload, size=8192):
            written_bytes += self._socket.send(segment)
        self._log(
            logging.DEBUG,
            f'Sent payload bytes: {written_bytes}, waiting for ACK: {self._sequence}')

    def _expected_ack_received(self):
        return self._last_ack == self._sequence

    def _read_ack(self):
        # first byte: read the version
        self._socket.recv(1)
        # second byte: frame type
        frame_type_packed = self._socket.recv(1)
        self._assert_frame_type_is_ack(frame_type_packed)

        received_ack = self._socket.recv(4)
        self._last_ack = unpack('>I', received_ack)[0]
        self._log(logging.DEBUG, f'Received ACK: {self._last_ack}')

    def _assert_frame_type_is_ack(self, frame_type_packed):
        if frame_type_packed:
            frame_type = unpack('B', frame_type_packed)[0]
            if frame_type == FRAME_TYPE_ACK:
                return
        else:
            frame_type = 0

        self._log(
            logging.WARNING,
            'Waited for ACK from server but received an unexpected frame: '
            f'"0x{frame_type:02X}". Aborting.')
        raise ConnectionException(f'No ACK received or wrong frame type "0x{frame_type:02X}"')
