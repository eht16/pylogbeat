# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the Apache License, Version 2.0 license.  See the LICENSE file for details.

from struct import pack
import logging

from tests.base import BaseTestCase, mock
from tests.fixture import MESSAGE, SOCKET_HOST, SOCKET_PORT, SOCKET_TIMEOUT
import pylogbeat


# pylint: disable=protected-access
# pylint: disable=no-member


class SendTest(BaseTestCase):

    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mock_ack_state = 'version'
        self._mock_ack_value = 3

    def test_send_success(self):
        with mock.patch.object(pylogbeat, 'LOGGER', new=self._mocked_logger):
            with mock.patch('pylogbeat.socket.socket'):
                client = self._factor_client()
                client.connect()

                # mock socket.recv(): version(2), frame type(A), ACK(2)
                window_size_packed = [b'2', b'A', b'\x00\x00\x00\x02']
                client._socket.recv.side_effect = window_size_packed

                client.send([MESSAGE, MESSAGE])

                client._socket.connect.assert_called_once_with((SOCKET_HOST, SOCKET_PORT))
                client._socket.settimeout.assert_called_once_with(SOCKET_TIMEOUT)
                # window size (replace frame type by 'W')
                window_size_packed[1] = b'W'
                client._socket.send.assert_any_call(b''.join(window_size_packed))
                # logger
                self._mocked_logger.log.assert_any_call(logging.DEBUG, 'Sent window size: 2')
                self._mocked_logger.log.assert_any_call(logging.DEBUG, 'Received ACK: 2')
                self._mocked_logger.reset_mock()

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
            use_logging=True)

    def test_send_failure_wrong_ack_frame_type(self):
        with mock.patch.object(pylogbeat, 'LOGGER', new=self._mocked_logger):
            with mock.patch('pylogbeat.socket.socket'):
                client = self._factor_client()
                client.connect()

                # mock socket.recv(): version(2), frame type(A), ACK(2)
                window_size_packed = [b'2', b'X', b'\x00\x00\x00\x02']
                client._socket.recv.side_effect = window_size_packed

                with self.assertRaises(pylogbeat.ConnectionException):
                    client.send([MESSAGE, MESSAGE])

                client._socket.connect.assert_called_once_with((SOCKET_HOST, SOCKET_PORT))
                client._socket.settimeout.assert_called_once_with(SOCKET_TIMEOUT)
                # window size (replace frame type by 'W')
                window_size_packed[1] = b'W'
                client._socket.send.assert_any_call(b''.join(window_size_packed))
                # logger
                self._mocked_logger.log.assert_any_call(logging.DEBUG, 'Sent window size: 2')
                self._mocked_logger.log.assert_any_call(
                    logging.WARNING,
                    'Waited for ACK from server but received an '
                    'unexpected frame: "0x58". Aborting.')
                self._mocked_logger.reset_mock()

    def test_send_failure_missing_ack_frame_type(self):
        with mock.patch.object(pylogbeat, 'LOGGER', new=self._mocked_logger):
            with mock.patch('pylogbeat.socket.socket'):
                client = self._factor_client()
                client.connect()

                # mock socket.recv(): empty response
                window_size_packed = [None, None, None]
                client._socket.recv.side_effect = window_size_packed

                with self.assertRaises(pylogbeat.ConnectionException):
                    client.send([MESSAGE, MESSAGE])

                client._socket.connect.assert_called_once_with((SOCKET_HOST, SOCKET_PORT))
                client._socket.settimeout.assert_called_once_with(SOCKET_TIMEOUT)
                window_size_packed = [b'2', b'W', b'\x00\x00\x00\x02']
                client._socket.send.assert_any_call(b''.join(window_size_packed))
                # logger
                self._mocked_logger.log.assert_any_call(logging.DEBUG, 'Sent window size: 2')
                self._mocked_logger.log.assert_any_call(
                    logging.WARNING,
                    'Waited for ACK from server but received an '
                    'unexpected frame: "0x00". Aborting.')
                self._mocked_logger.reset_mock()

    def test_send_failure_wrong_ack(self):
        with mock.patch.object(pylogbeat, 'LOGGER', new=self._mocked_logger):
            with mock.patch('pylogbeat.socket.socket'):
                client = self._factor_client()
                client.connect()
                # mock the socket to send multiple ACK responses with some wrong ACK sequences
                # and finally the correct one to test waiting for the correct ACK sequence
                client._socket.recv.side_effect = self._simulate_recv_ack_responses

                client.send([MESSAGE, MESSAGE])

                client._socket.connect.assert_called_once_with((SOCKET_HOST, SOCKET_PORT))
                client._socket.settimeout.assert_called_once_with(SOCKET_TIMEOUT)
                if hasattr(client._socket.recv, 'assert_called'):
                    # current pypy3 is 3.5 and so doesn't have assert_called()
                    client._socket.recv.assert_called()
                # window size (replace frame type by 'W')
                window_size_packed = [b'2', b'W', b'\x00\x00\x00\x02']
                client._socket.send.assert_any_call(b''.join(window_size_packed))
                # logger
                self._mocked_logger.log.assert_any_call(logging.DEBUG, 'Sent window size: 2')
                self._mocked_logger.reset_mock()

    def _simulate_recv_ack_responses(self, read_length):
        if self._mock_ack_state == 'version' and read_length == 1:
            self._mock_ack_state = 'frame_type'
            return b'2'
        if self._mock_ack_state == 'frame_type' and read_length == 1:
            self._mock_ack_state = 'ack'
            return b'A'
        if self._mock_ack_state == 'ack' and read_length == 4:
            self._mock_ack_state = 'version'
            self._mock_ack_value = 2 if self._mock_ack_value == 9 else self._mock_ack_value + 1
            return pack('>I', self._mock_ack_value)

        return b''
