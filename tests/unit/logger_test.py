# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the Apache License, Version 2.0 license.  See the LICENSE file for details.

import logging
import sys

from tests.base import BaseTestCase, mock
import pylogbeat


# pylint: disable=protected-access


class LoggerTest(BaseTestCase):

    def test_logging_enabled(self):

        with mock.patch.object(pylogbeat, 'LOGGER', new=self._mocked_logger):
            client = self._factor_client(use_logging=True)
            log_level = logging.INFO
            log_message = 'test'
            # test
            client._log(log_level, log_message)
            # check
            self._mocked_logger.log.assert_called_once_with(log_level, log_message)
            self._mocked_logger.reset_mock()

    def _factor_client(self, use_logging):
        return pylogbeat.PyLogBeatClient(
            host=None,
            port=None,
            timeout=None,
            ssl_enable=False,
            ssl_verify=True,
            keyfile=None,
            certfile=None,
            ca_certs=None,
            use_logging=use_logging)

    def test_logging_disabled_info(self):

        with mock.patch.object(pylogbeat, 'LOGGER', new=self._mocked_logger):
            client = self._factor_client(use_logging=False)
            log_level = logging.INFO
            log_message = 'test'
            # test
            client._log(log_level, log_message)

            # check - logger not touched
            self._mocked_logger.log.assert_not_called()
            self._mocked_logger.reset_mock()

            # check - nothing on stdout
            output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
            self.assertEqual(output, '')

            # check - nothing on stderr with level INFO
            output = sys.stderr.getvalue().strip()  # pylint: disable=no-member
            self.assertEqual(output, '')

    def test_logging_disabled_error(self):

        with mock.patch.object(pylogbeat, 'LOGGER', new=self._mocked_logger):
            client = self._factor_client(use_logging=False)
            log_level = logging.WARNING
            log_message = 'test'
            # test
            client._log(log_level, log_message)

            # check - logger not touched
            self._mocked_logger.log.assert_not_called()
            self._mocked_logger.reset_mock()

            # check - nothing on stdout
            output = sys.stdout.getvalue().strip()  # pylint: disable=no-member
            self.assertEqual(output, '')

            # check - log_message on stderr with level WARNING
            output = sys.stderr.getvalue().strip()  # pylint: disable=no-member
            self.assertIn(logging.getLevelName(log_level), output)
            self.assertIn(log_message, output)
