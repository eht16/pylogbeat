# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the Apache License, Version 2.0 license.  See the LICENSE file for details.

from unittest import mock  # noqa pylint: disable=unused-import
import logging
import unittest


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()

        # provide a mocked logger for easy use
        self._mocked_logger = mock.MagicMock(spec=logging)
