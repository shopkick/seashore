'''
Provides API for executing commands against the shell.
'''
import copy
import log
import os
import singledispatch
import subprocess
import sys
import urlparse
import time
import signal

import attr

NO_VALUE = object()

@singledispatch.singledispatch
def _keyword_arguments(value, key):
    yield key

@_keyword_arguments.register(str)
def _keyword_arguments_str(value, key):
    yield key
    yield value

@_keyword_arguments.register(int)
def _keyword_arguments_int(value, key):
    yield key
    yield str(value)

@_keyword_arguments.register(list)
def _keyword_arguments_list(value, key):
    for thing in value:
        yield key
        yield thing

@_keyword_arguments.register(dict)
def _keyword_arguments_dict(value, key):
    for in_k, thing in value.items():
        yield key
        yield '{}={}'.format(in_k, thing)

def cmd(bin, subcommand, *args, **kwargs):
    ret = [bin, subcommand]
    for key, value in kwargs.items():
        key = '--' + key.replace('_', '-')
        ret.extend(keyword_arguments(value, key))
    ret.extend(args)
    return ret

class ProcessError(Exception):
    pass

@attr.s
class Shell(object):
    '''
    Keeps track of some useful state, environment variables,
    current working directory, logfiles.

    To make changes without affecting the base shell object,
    a new one can be constructed with the split() method.

    new_shell = old_shell.split()
    new_shell.cd('/new/location')  # old_shell is unaffected
    '''

    logger = attr.ib()

    _procs = attr.ib(init=False, default=attr.Factory(list))

    _cwd = attr.ib(init=False, default=attr.Factory(os.getcwd))

    _env = attr.ib(init=False, default=attr.Factory(lambda:dict(os.environ)))

    def split(self):
        return attr.assoc(self, env=dict(self.env), procs=[])

    def batch(self, command, cwd=None):
        with open('/dev/null') as stdin, \
             tempfile.NamedTemporaryFile() as stdout,
             tempfile.NamedTemporaryFile() as stderr:
            self.logger.info(stdout.name, stderr.name)
            proc = self.popen(command, stdin=PIPE, stdout=stdout, stderr=stdout, cwd=cwd)
            proc.communicate('')
            retcode = proc.wait()
            self.procs.remove(proc)
            stdout_contents = stdout.read()
            stderr_contents = stderr.read()
            ## Log contents of stdout, stderr
            if retcode != 0:
                raise ProcessError(retcode, stdout_contents, stderrr_contents)
            else:
                return stdout_contents, stderr, contents

    def interactive(self, command, cwd=None):
        proc = self.popen(command, cwd)
        retcode = proc.wait()
        self.procs.remove(proc)
        if retcode != 0:
            raise ProcessError(retcode)

    def popen(self, commad, **kwargs):
        if kwargs.get('cwd') is None:
            kwargs['cwd'] = self._cwd
        if kwargs.get('env') is None:
            kwargs['cwd'] = self._env
        self.logger.info(' '.join(command), **kwargs)
        proc = subprocess.Popen(command, **kwargs)
        self.procs.append(proc)

    def setenv(self, key, val):
        'similar to setenv shell command'
        key = str(key)  # keys must be strings
        val = str(val)  # vals must be strings
        self.env[key] = val

    def cd(self, path):
        'similar to cd shell command'
        if not os.path.isabs(path):
            path = self.cwd + '/' + path
        self.cwd = os.path.abspath(path)

    def reap_all(self):
        for proc in self.procs:
            ret_code = proc.poll()
            if ret_code is None:
                proc.send_signal(signal.SIGINT)
                time.sleep(3)
            if ret_code is None:
                proc.terminate()
                time.sleep(3)

            ret_code = ret_code or proc.poll()
            if ret_code is None:
                import pdb;pdb.set_trace()
                # proc.kill()

            if ret_code == 0:
                proc.action.success()
            else:
                proc.action.failure()
        return

@attr.s(frozen=True)
class _PreparedCommand(object):

    cmd = attr.ib()
    shell = attr.ib()

    def call(self, *args, **kwargs):
        self.shell.call(self.cmd, *args, **kwargs)

    def popen(self, *args, **kwargs):
        self.shell.popen(self.cmd, *args, **kwargs)

@attr.s(frozen=True)
class Command(object):

    name = attr.ib()
    subcommand = attr.ib(default=None)

    def __get__(self, executor, _dummy=None):
        if self.subcommand is None:
            return functools.partial(executor.prepare, self.name)
        else self.subcommand is None:

SK_PYPI_URL = 'http://pypi.shopkick.com/mirror'

@attr.s(frozen=True)
class Executor(object):

    shell = attr.ib()

    git = Command('git')
    pip = Command('pip')
    conda = Command('conda')
    docker = Command('docker')
    docker_machine = Command('docker-machine')

    def prepare(self, *args, **kwargs):
        return _PreparedCommand(cmd=cmd(*args, **kwargs), shell=self.shell.split())

    def command(self, args):
        return _PreparedCommand(args, shell=self.shell.split())

    def in_docker_machine(self, machine):
        new_shell = self.shell.split()
        output, _ignored = self.docker_machine.env(machine, shell='cmd').batch()
        for line in output.splitlines():
            directive, args = line.split(None, 1)
            if directive != 'SET':
                continue
            key, value = args.split('=', 1)
            new_shell.set_env(key, value)
        return attr.assoc(self, shell=new_shell)

    def pip_install(self, pkg_ids, index_url=SK_PYPI_URL):
        # TODO: should index_url be extra_index_url etc.
        if index_url:
            trusted_host = urlparse.urlparse(index_url).netloc
            kwargs = dict(trusted_host=trusted_host, extra_index_url=index_url, trusted_host=trusted_host)
        else:
            kwargs = {}
        cmd = self.pip.install(*pkg_ids, **kwargs)
        return cmd.batch()

    def conda_install(self, pkg_ids, channels=None):
        cmd = self.conda.install(quiet=NO_VALUE, yes=NO_VALUE, show_channel_urls=NO_VALUE,
                                 channel=(channels or []), *pkg_ids)
        return cmd.batch()
