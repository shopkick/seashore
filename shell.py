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

import attr

SK_PYPI_URL = 'http://pypi.shopkick.com/mirror'

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

def mkcommand(bin):
    return functools.partial(cmd, bin)


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
    sky_path, logger = attr.ib(), attr.ib()

    @classmethod
    def split(self):
        clone = copy.copy(self)
        clone.env = dict(self.env)

    def __attrs_post_init__(self):
        self.outfile = open(self.sky_path + '/shell.txt', 'ab')
        self.env = dict(os.environ)
        self.cwd = os.getcwd()
        self.procs = []

    def call(self, command, return_output=False, 
             expecting_output=False, autoexit=True, **proc_args):
        '''
        return_output -- if the output from the command should
        expecting_output -- if the command is expected to have output
           (used to make better line-wrapping behavior)
        be returned as a string or sent to stdout logfile
        '''
        subprocess_args = {
            # shell=True for string commands, False for list
            "shell": isinstance(command, basestring),
            "stdout": self.outfile,
            "stderr": self.outfile,
            "cwd": self.cwd,
            "env": self.env}
        subprocess_args.update(**proc_args)
        log_args = {}
        if subprocess_args['stdout'] is not self.outfile:
            if subprocess_args['stdout'] is not None:
                log_args['stdout'] = subprocess_args['stdout'].name
        autoexit_code = None
        if isinstance(command, basestring):
            log_name = command
        else:
            log_name = ' '.join(command)
        with self.logger.info(log_name, **log_args) as act:
            if expecting_output and not return_output:
                print ''  # force logging to newline
            self.outfile.write("### {} \n".format(repr(command)))
            self.outfile.flush()
            if return_output:
                func = subprocess.check_output
                subprocess_args.pop('stdout')
                subprocess_args.pop('stderr')
            else:
                func = subprocess.check_call
            act.data_map.update(subprocess_args)
            act.data_map.pop('env', None)
            act.data_map.pop('shell', None)
            try:
                return func(command, **subprocess_args)
            except subprocess.CalledProcessError as cpe:
                act['return_code'] = cpe.returncode
                if autoexit:
                    autoexit_code = cpe.returncode
                act.failure("command {action_name} exited with status {return_code} (output: {!r}) {data_map_repr}", cpe.output)

        if autoexit_code:
            sys.exit(autoexit_code)

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

    def popen(self, command, **proc_args):
        subprocess_args = {
            "shell": isinstance(command, basestring),
            "stdout": self.outfile,
            "stderr": self.outfile,
            "cwd": self.cwd,
            "env": self.env}
        subprocess_args.update(**proc_args)
        action = self.logger.info(command, stdout=subprocess_args['stdout'].name)
        action.begin()
        self.outfile.write("\n### {} \n".format(command))
        self.outfile.flush()
        proc = subprocess.Popen(command, **subprocess_args)
        proc.action = action
        
        self.procs.append(proc)

        return proc

    def log_file(self, path):
        if os.path.exists(path):
            lines = list(open(path))
            self.outfile.write('### file {0} ({1} lines):\n'.format(path, len(lines)))
            self.outfile.write(''.join(lines))
            self.outfile.write('### end file {0}\n'.format(path))

    def reap_all(self):
        import time
        import signal
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


class Executor(object):

    git = mkcommand('git')
    pip = mkcommand('pip')
    conda = mkcommand('conda')
    docker = mkcommand('docker')
    docker_machine = mkcommand('docker-machine')

    def __init__(self):
        self.shell = shell

    def prepare(self, *args, **kwargs):
        return _PreparedCommand(cmd=cmd(*args, **kwargs), shell=self.shell.split())

    def command(self, args):
        return _PreparedCommand(args, shell=self.shell.split())

    def in_docker_machine(self, machine):
        new_shell = self.shell.split()
        cmd = self.prepare('docker-machine', 'env', machine, shell='cmd')
        output = cmd.call(return_output=True)
        for line in output.splitlines():
            directive, args = line.split(None, 1)
            if directive != 'SET':
                continue
            key, value = args.split('=', 1)
            new_shell.set_env(key, value)
        return attr.assoc(self, shell=new_shell)

    def pip_install(self, pkg_ids, index_url=SK_PYPI_URL, **proc_args):
        # TODO: should index_url be extra_index_url etc.
        if index_url:
            trusted_host = urlparse.urlparse(index_url).netloc
            cmd = self.prepare('pip', 'install',
                                *pkg_ids, extra_index_url=index_url, trusted_host=trusted_host)
        else:
            cmd = self.prepare('pip', 'install', *pkg_ids)
        return cmd.call(**proc_args)

    def conda_install(self, pkg_ids, channels=None, **proc_args):
        cmd = self.prepare('install', quiet=NO_VALUE, yes=NO_VALUE, show_channel_urls=NO_VALUE,
                                     channel=(channels or []), *pkg_ids)
        return cmd.call(**proc_args)
