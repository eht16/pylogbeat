# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the Apache License, Version 2.0 license.  See the LICENSE file for details.

import logging

from mocket.mocket import Mocket, MocketEntry, mocketize

from tests.base import BaseTestCase, mock
from tests.fixture import MESSAGE, SOCKET_HOST, SOCKET_PORT, SOCKET_TIMEOUT
import pylogbeat


# pylint: disable=protected-access
# pylint: disable=no-member


class IntegrationTest(BaseTestCase):

    @mocketize
    def test_ok(self):
        # window size (we will send two messages below, so let's answer with two)
        response = b'2A\x00\x00\x00\x02'
        Mocket.register(MocketEntry((SOCKET_HOST, SOCKET_PORT), [response]))

        client = self._factor_client()
        try:
            client.send([MESSAGE, MESSAGE])
        finally:
            client.close()

        self.assertEqual(len(Mocket._requests), 1)

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

    @mocketize
    def test_wrong_ack_end_of_stream(self):
        # respond with wrong ACK sequence
        response = b'2A\x00\x00\x00\x03'
        Mocket.register(MocketEntry((SOCKET_HOST, SOCKET_PORT), [response]))

        client = self._factor_client()
        try:
            # on real sockets, here we would expect a timeout or no data;
            # Mocket raises BlockingIOError
            with self.assertRaises(BlockingIOError):
                client.send([MESSAGE, MESSAGE])
        finally:
            client.close()

        self.assertEqual(len(Mocket._requests), 1)

    @mocketize
    def test_wrong_ack_additional_answer(self):
        with mock.patch.object(pylogbeat, 'LOGGER', new=self._mocked_logger):
            # respond with wrong ACK sequence
            response = b'2A\\x00\x00\x00\x03\x03\x03'
            Mocket.register(MocketEntry((SOCKET_HOST, SOCKET_PORT), [response]))

            exc = None
            client = self._factor_client()
            try:
                with self.assertRaises(pylogbeat.ConnectionException) as exc:
                    client.send([MESSAGE, MESSAGE])
            finally:
                client.close()

            if exc is not None:
                message = str(exc.exception)
                expected_message = 'No ACK received or wrong frame type "0x00"'
                self.assertEqual(message, expected_message)

            self.assertEqual(len(Mocket._requests), 1)
            # logger
            self._mocked_logger.log.assert_any_call(
                logging.WARNING,
                'Waited for ACK from server but received an unexpected frame: "0x00". Aborting.')
            self._mocked_logger.reset_mock()
