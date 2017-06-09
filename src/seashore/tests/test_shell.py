# Copyright (c) Shopkick 2017
# See LICENSE for details.
"""Tests for seashore.shell"""

import sys
import tempfile
import unittest

from seashore import shell

class ShellTest(unittest.TestCase):

    """Tests for Shell()"""

    def setUp(self):
        """create a new shell object"""
        self.shell = shell.Shell()

    def test_redirect(self):
        """redirect sends output to temp file"""
        python_script = "import sys;sys.stdout.write('hello');sys.stderr.write('goodbye')"
        with tempfile.NamedTemporaryFile() as stdout, \
             tempfile.NamedTemporaryFile() as stderr:
            self.shell.redirect([sys.executable, '-c', python_script], stdout, stderr)
            stdout.seek(0)
            out = stdout.read()
            stderr.seek(0)
            err = stderr.read()
        self.assertEquals(out, b'hello')
        self.assertEquals(err, b'goodbye')

    def test_failed_redirect(self):
        """redirect sends output to temp file and raises if it fails"""
        python_script = ("import sys;sys.stdout.write('hello');sys.stderr.write('goodbye');"
                         "sys.exit(1)")
        with tempfile.NamedTemporaryFile() as stdout, \
             tempfile.NamedTemporaryFile() as stderr:
            with self.assertRaises(shell.ProcessError):
                self.shell.redirect([sys.executable, '-c', python_script], stdout, stderr)
            stdout.seek(0)
            out = stdout.read()
            stderr.seek(0)
            err = stderr.read()
        self.assertEquals(out, b'hello')
        self.assertEquals(err, b'goodbye')

    def test_batch(self):
        """batch mode returns contents of stdout/stderr from subprocesses"""
        python_script = "import sys;sys.stdout.write('hello');sys.stderr.write('goodbye')"
        out, err = self.shell.batch([sys.executable, '-c', python_script])
        self.assertEquals(out, b'hello')
        self.assertEquals(err, b'goodbye')

    def test_failed_batch(self):
        """processes exiting with non-zero code causes an exception in batch mode"""
        python_script = b"raise SystemExit(1)"
        with self.assertRaises(shell.ProcessError):
            self.shell.batch([sys.executable, '-c', python_script])

    def test_failed_interactive(self):
        """processes exiting with non-zero code causes an exception in interactive mode"""
        python_script = "raise SystemExit(1)"
        with self.assertRaises(shell.ProcessError):
            self.shell.interactive([sys.executable, '-c', python_script])

    def test_env(self):
        """setting an environment variable in the shell propagates to subprocesses"""
        self.shell.setenv('SPECIAL', 'emett')
        python_script = b'import sys,os;sys.stdout.write(os.environ["SPECIAL"])'
        out, _ignored = self.shell.batch([sys.executable, '-c', python_script])
        self.assertEquals(out, b'emett')
        self.assertEquals(self.shell.getenv('SPECIAL'), 'emett')

    def test_chdir(self):
        """changing the shell's directory effects the cwd of processes it runs"""
        self.shell.chdir('/')
        python_script = b'import sys,os;sys.stdout.write(os.getcwd())'
        out, _ignored = self.shell.batch([sys.executable, b'-c', python_script])
        self.assertEquals(out, b'/')

    def test_reaper(self):
        """killing a process terminates it with a negative signal"""
        python_script = b'import time;time.sleep(100000)'
        proc = self.shell.popen([sys.executable, b'-c', python_script])
        self.shell.reap_all()
        self.assertLess(proc.wait(), 0)

    def test_clone(self):
        """cloned shell's environment does not interfere with the original"""
        new_shell = self.shell.clone()
        new_shell.setenv('SPECIAL', 'lucy')
        self.shell.setenv('SPECIAL', 'emett')
        python_script = b'import sys,os;sys.stdout.write(os.environ["SPECIAL"])'
        out, _ignored = new_shell.batch([sys.executable, '-c', python_script])
        self.assertEquals(out, b'lucy')

class ProcessErrorTest(unittest.TestCase):

    """Tests that check process error is useful"""

    def test_returncode(self):
        """returncode attribtue is set to passed-in value"""
        self.assertEquals(shell.ProcessError(13).returncode, 13)

    def test_output(self):
        """output attribtue is set to passed-in value"""
        self.assertEquals(shell.ProcessError(13, "woo").output, "woo")

    def test_repr(self):
        """repr contains output, error and code"""
        procerr = shell.ProcessError(13, "myout", "myerr")
        stringified = repr(procerr)
        self.assertIn('13', stringified)
        self.assertIn('myout', stringified)
        self.assertIn('myerr', stringified)

class AutoexitTest(unittest.TestCase):

    """Tests for autoexit_code"""

    def test_success(self):
        """autoexit_code wrapping success does not exit"""
        with shell.autoexit_code():
            pass
        self.addCleanup(lambda: None)

    def test_failure(self):
        """autoexit_code wrapping a ProcessError raise exits"""
        with self.assertRaises(SystemExit):
            with shell.autoexit_code():
                raise shell.ProcessError(13)
