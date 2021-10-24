# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the Apache License, Version 2.0 license.  See the LICENSE file for details.

import socket
import ssl

from tests.base import BaseTestCase, mock
from tests.fixture import (
    SOCKET_HOST,
    SOCKET_PORT,
    SOCKET_TIMEOUT,
    SSL_CACERTS,
    SSL_CERTFILE,
    SSL_KEYFILE,
)
import pylogbeat


# pylint: disable=protected-access
# pylint: disable=no-member


class SocketTest(BaseTestCase):

    def test_socket_connect_no_ssl(self):
        with mock.patch('pylogbeat.socket.socket'):
            with mock.patch('pylogbeat.ssl') as ssl_mock:
                client = self._factor_client(ssl_enable=False, timeout=SOCKET_TIMEOUT)
                client.connect()

                client._socket.connect.assert_called_once_with((SOCKET_HOST, SOCKET_PORT))
                client._socket.settimeout.assert_called_once_with(SOCKET_TIMEOUT)

                ssl_mock.create_default_context.assert_not_called()

    def test_socket_connect_no_ssl_no_timeout(self):
        with mock.patch('pylogbeat.socket.socket'):
            with mock.patch('pylogbeat.ssl') as ssl_mock:
                client = self._factor_client(ssl_enable=False, timeout=None)
                client.connect()

                client._socket.connect.assert_called_once_with((SOCKET_HOST, SOCKET_PORT))
                client._socket.settimeout.assert_not_called()

                ssl_mock.create_default_context.assert_not_called()

    def _factor_client(self, ssl_enable, ssl_verify=True, timeout=None):
        return pylogbeat.PyLogBeatClient(
            host=SOCKET_HOST,
            port=SOCKET_PORT,
            timeout=timeout,
            ssl_enable=ssl_enable,
            ssl_verify=ssl_verify,
            keyfile=SSL_KEYFILE,
            certfile=SSL_CERTFILE,
            ca_certs=SSL_CACERTS,
            use_logging=True)

    def test_socket_connect_with_ssl_verify_true(self):
        with mock.patch('pylogbeat.socket.socket') as socket_mock:
            with mock.patch('pylogbeat.ssl') as ssl_mock:
                default_context_mock = mock.MagicMock(spec=ssl.SSLContext)
                ssl_mock.create_default_context.return_value = default_context_mock

                client = self._factor_client(ssl_enable=True, ssl_verify=True)
                client.connect()

                mocked_socket = socket_mock(socket.AF_INET, socket.SOCK_STREAM)

                mocked_socket.connect.assert_called_once_with((SOCKET_HOST, SOCKET_PORT))
                mocked_socket.settimeout.assert_not_called()

                ssl_mock.create_default_context.assert_called_once_with(cafile=SSL_CACERTS)
                self.assertEqual(default_context_mock.verify_mode, ssl_mock.CERT_REQUIRED)
                self.assertFalse(default_context_mock.check_hostname)
                default_context_mock.load_cert_chain.assert_called_once_with(
                    SSL_CERTFILE, SSL_KEYFILE)
                default_context_mock.wrap_socket.assert_called_once_with(
                    mocked_socket,
                    server_side=False)

    def test_socket_connect_with_ssl_verify_false(self):
        with mock.patch('pylogbeat.socket.socket') as socket_mock:
            with mock.patch('pylogbeat.ssl') as ssl_mock:
                default_context_mock = mock.MagicMock(spec=ssl.SSLContext)
                ssl_mock.create_default_context.return_value = default_context_mock

                client = self._factor_client(ssl_enable=True, ssl_verify=False)
                client.connect()

                mocked_socket = socket_mock(socket.AF_INET, socket.SOCK_STREAM)

                mocked_socket.connect.assert_called_once_with((SOCKET_HOST, SOCKET_PORT))
                mocked_socket.settimeout.assert_not_called()

                ssl_mock.create_default_context.assert_called_once_with(cafile=SSL_CACERTS)
                self.assertEqual(default_context_mock.verify_mode, ssl_mock.CERT_OPTIONAL)
                self.assertFalse(default_context_mock.check_hostname)
                default_context_mock.load_cert_chain.assert_called_once_with(
                    SSL_CERTFILE, SSL_KEYFILE)
                default_context_mock.wrap_socket.assert_called_once_with(
                    mocked_socket,
                    server_side=False)

    def test_socket_close(self):
        with mock.patch.object(pylogbeat, 'LOGGER', new=self._mocked_logger):
            with mock.patch('pylogbeat.socket.socket'):
                client = self._factor_client(ssl_enable=False)
                client.connect()
                client._socket.connect.assert_called_once_with((SOCKET_HOST, SOCKET_PORT))
                # close existing socket
                client.close()
                self.assertIsNone(client._socket)

                # close already closed socket
                client.close()
                self.assertIsNone(client._socket)
