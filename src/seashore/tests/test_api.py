import sys
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

    def test_batch(self):
        python_script = "import sys;sys.stdout.write('hello');sys.stderr.write('goodbye')"
        out, err = self.shell.batch([sys.executable, '-c', python_script])
        self.assertEquals(out, 'hello')
        self.assertEquals(err, 'goodbye')

    def test_failed_batch(self):
        python_script = "raise SystemExit(1)"
        with self.assertRaises(api.ProcessError):
            self.shell.batch([sys.executable, '-c', python_script])

    def test_failed_interactive(self):
        python_script = "raise SystemExit(1)"
        with self.assertRaises(api.ProcessError):
            self.shell.interactive([sys.executable, '-c', python_script])
