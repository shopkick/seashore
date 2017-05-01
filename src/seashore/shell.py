'''
Provides API for executing commands against the shell.
'''
import copy
import contextlib
import os
import singledispatch
import subprocess
import sys
import urlparse
import time
import signal
import tempfile

import attr


class ProcessError(Exception):
    pass

@attr.s
class Shell(object):

    logger = attr.ib()

    _procs = attr.ib(init=False, default=attr.Factory(list))

    _cwd = attr.ib(init=False, default=attr.Factory(os.getcwd))

    _env = attr.ib(init=False, default=attr.Factory(lambda:dict(os.environ)))

    def batch(self, command, cwd=None):
        with open('/dev/null') as stdin, \
             tempfile.NamedTemporaryFile() as stdout, \
             tempfile.NamedTemporaryFile() as stderr:
            self.logger.info(stdout.name, stderr.name)
            proc = self.popen(command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, cwd=cwd)
            proc.communicate('')
            retcode = proc.wait()
            self._procs.remove(proc)
            stdout.seek(0)
            stderr.seek(0)
            stdout_contents = stdout.read()
            stderr_contents = stderr.read()
            ## Log contents of stdout, stderr
            if retcode != 0:
                raise ProcessError(retcode, stdout_contents, stderr_contents)
            else:
                return stdout_contents, stderr_contents

    def interactive(self, command, cwd=None):
        proc = self.popen(command, cwd=cwd)
        retcode = proc.wait()
        self._procs.remove(proc)
        if retcode != 0:
            raise ProcessError(retcode)

    def popen(self, command, **kwargs):
        if kwargs.get('cwd') is None:
            kwargs['cwd'] = self._cwd
        if kwargs.get('env') is None:
            kwargs['env'] = self._env
        self.logger.info(' '.join(command), **kwargs)
        proc = subprocess.Popen(command, **kwargs)
        self._procs.append(proc)
        return proc

    def setenv(self, key, val):
        'similar to setenv shell command'
        key = str(key)  # keys must be strings
        val = str(val)  # vals must be strings
        self._env[key] = val

    def cd(self, path):
        'similar to cd shell command'
        self._cwd = os.path.join(self._cwd, path)

    def reap_all(self):
        for proc in self._procs:
            ret_code = proc.poll()
            if ret_code is None:
                proc.send_signal(signal.SIGINT)
                time.sleep(3)
            ret_code = ret_code or proc.poll()
            if ret_code is None: # pragma: no coverage
                proc.terminate()
                time.sleep(3)
            ret_code = ret_code or proc.poll() # pragma: no coverage
            if ret_code is None: # pragma: no coverage
                proc.kill()

    def clone(self):
        return attr.assoc(self, _env=dict(self._env), _procs=[])

@contextlib.contextmanager
def autoexit_code():
    try:
        yield
    except ProcessError as pe:
        raise SystemExit(pe[0])
