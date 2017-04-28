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

    def test_env(self):
        self.shell.setenv('SPECIAL', 'emett')
        python_script = 'import sys,os;sys.stdout.write(os.environ["SPECIAL"])'
        out, _ignored = self.shell.batch([sys.executable, '-c', python_script])
        self.assertEquals(out, 'emett')

    def test_cd(self):
        self.shell.cd('/')
        python_script = 'import sys,os;sys.stdout.write(os.getcwd())'
        out, _ignored = self.shell.batch([sys.executable, '-c', python_script])
        self.assertEquals(out, '/')

    def test_reaper(self):
        python_script = 'import time;time.sleep(100000)'
        proc = self.shell.popen([sys.executable, '-c', python_script])
        self.shell.reap_all()
        self.assertLess(proc.wait(), 0)

    def test_clone(self):
        new_shell = self.shell.clone()
        new_shell.setenv('SPECIAL', 'lucy')
        self.shell.setenv('SPECIAL', 'emett')
        python_script = 'import sys,os;sys.stdout.write(os.environ["SPECIAL"])'
        out, _ignored = new_shell.batch([sys.executable, '-c', python_script])
        self.assertEquals(out, 'lucy')
