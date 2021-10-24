# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the Apache License, Version 2.0 license.  See the LICENSE file for details.

from tests.base import BaseTestCase, mock
from tests.fixture import MESSAGE, MESSAGE_JSON, SOCKET_HOST, SOCKET_PORT, SOCKET_TIMEOUT
import pylogbeat


# pylint: disable=protected-access
# pylint: disable=no-member


class InputTest(BaseTestCase):

    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mock_ack_state = 'version'
        self._mock_ack_value = 3

    def _factor_client(self):
        return pylogbeat.PyLogBeatClient(
            host=SOCKET_HOST,
            port=SOCKET_PORT,
            timeout=SOCKET_TIMEOUT,
            ssl_enable=False,
            ssl_verify=True,
            keyfile=None,
            certfile=None,
            ca_certs=None,
            use_logging=False)

    def test_valid_input_empty_list(self):
        self._test_valid_input([])

    def _test_valid_input(self, valid_value):
        with mock.patch('pylogbeat.socket.socket'):
            client = self._factor_client()
            client.connect()
            # calculate ACK
            value_len = len(valid_value)
            ack = f'\x00\x00\x00{chr(value_len)}'
            # mock socket.recv(): version(2), frame type(A), ACK(1)
            window_size_packed = [b'2', b'A', ack.encode('ascii')]
            client._socket.recv.side_effect = window_size_packed
            client.send(valid_value)
            client._socket.connect.assert_called_once_with((SOCKET_HOST, SOCKET_PORT))

    def test_valid_input_empty_tuple(self):
        self._test_valid_input(())

    def test_valid_input_empty_set(self):
        self._test_valid_input(set([]))

    def test_valid_input_dict(self):
        self._test_valid_input([MESSAGE])

    def test_valid_input_string(self):
        self._test_valid_input([MESSAGE_JSON])

    def test_invalid_input_bytes_list(self):
        self._test_valid_input([MESSAGE_JSON.encode('ascii')])

    def test_valid_input_multi_elements(self):
        elements = [
            MESSAGE,
            MESSAGE_JSON]
        self._test_valid_input(elements)

    def test_invalid_input_none(self):
        self._test_invalid_input(None)

    def _test_invalid_input(self, invalid_value):
        with mock.patch('pylogbeat.socket.socket'):
            client = self._factor_client()
            client.connect()

        with self.assertRaises(TypeError):
            client.send(invalid_value)

    def test_invalid_input_empty_dict(self):
        self._test_invalid_input({})

    def test_invalid_input_dict(self):
        self._test_invalid_input({'foo': 'bar'})

    def test_invalid_input_empty_element(self):
        self._test_invalid_input([None])

    def test_invalid_input_nested_list(self):
        self._test_invalid_input([[1, 2, 3]])

    def test_invalid_input_string(self):
        self._test_invalid_input(MESSAGE_JSON)

    def test_invalid_input_bytes(self):
        self._test_invalid_input(MESSAGE_JSON.encode('ascii'))

    def test_invalid_input_number(self):
        self._test_invalid_input(42)

    def test_invalid_some_object_mock(self):
        self._test_invalid_input(mock)

    def test_invalid_some_object_exception(self):
        self._test_invalid_input(TypeError())
