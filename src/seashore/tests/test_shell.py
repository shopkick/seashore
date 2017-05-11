import sys
import unittest

import attr

from seashore import shell

@attr.s
class DummyLogger(object):

    _messages = attr.ib()

    def info(self, *args, **kwargs):
        self._messages.append(('info', args, kwargs))

class ShellTest(unittest.TestCase):

    def setUp(self):
        self.shell = shell.Shell()

    def test_batch(self):
        python_script = "import sys;sys.stdout.write('hello');sys.stderr.write('goodbye')"
        out, err = self.shell.batch([sys.executable, '-c', python_script])
        self.assertEquals(out, 'hello')
        self.assertEquals(err, 'goodbye')

    def test_failed_batch(self):
        python_script = "raise SystemExit(1)"
        with self.assertRaises(shell.ProcessError):
            self.shell.batch([sys.executable, '-c', python_script])

    def test_failed_interactive(self):
        python_script = "raise SystemExit(1)"
        with self.assertRaises(shell.ProcessError):
            self.shell.interactive([sys.executable, '-c', python_script])

    def test_env(self):
        self.shell.setenv(b'SPECIAL', b'emett')
        python_script = b'import sys,os;sys.stdout.write(os.environ["SPECIAL"])'
        out, _ignored = self.shell.batch([sys.executable, b'-c', python_script])
        self.assertEquals(out, b'emett')
        self.assertEquals(self.shell.getenv(b'SPECIAL'), b'emett')

    def test_cd(self):
        self.shell.cd(b'/')
        python_script = b'import sys,os;sys.stdout.write(os.getcwd())'
        out, _ignored = self.shell.batch([sys.executable, b'-c', python_script])
        self.assertEquals(out, b'/')

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

class AutoexitTest(unittest.TestCase):

    def test_success(self):
        with shell.autoexit_code():
            pass

    def test_failure(self):
        with self.assertRaises(SystemExit):
            with shell.autoexit_code():
                raise shell.ProcessError(13)
