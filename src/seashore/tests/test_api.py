import unittest

import attr

from seashore import api

@attr.s
class DummyLogger(object):

    _messages = attr.ib()

    def info(self, *args, **kwargs):
        self._messages.append(('info', args, kwargs))

class ShellTest(unittest.TestCase):

    def setUp(self):
        self.messages = []
        self.logger = DummyLogger(self.messages)
        self.shell = api.Shell(self.logger)

    def test_nothing(self):
        pass
