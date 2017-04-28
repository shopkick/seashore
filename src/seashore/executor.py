import functools

import singledispatch

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
        ret.extend(_keyword_arguments(value, key))
    ret.extend(args)
    return ret

@attr.s(frozen=True)
class _PreparedCommand(object):

    cmd = attr.ib()
    shell = attr.ib()

    def batch(self, *args, **kwargs):
        return self.shell.batch(self.cmd, *args, **kwargs)

    def interactive(self, *args, **kwargs):
        return self.shell.interactive(self.cmd, *args, **kwargs)

    def popen(self, *args, **kwargs):
        return self.shell.popen(self.cmd, *args, **kwargs)

@attr.s(frozen=True)
class Command(object):

    name = attr.ib()

    def bind(self, executor, _dummy=None):
        return _ExecutoredCommand(executor, self.name)

    __get__ = bind

@attr.s(frozen=True)
class _ExecutoredCommand(object):

    _executor = attr.ib()

    _name = attr.ib()

    def __call__(self, *args, **kwargs):
        return self._executor.prepare(self._name, *args, **kwargs)

    def __getattr__(self, subcommand):
        return functools.partial(self._executor.prepare, self._name, subcommand)

@attr.s(frozen=True)
class Executor(object):

    shell = attr.ib()
    pypi = attr.ib(default=None)
    _commands = attr.ib(default=attr.Factory(set))

    git = Command('git')
    pip = Command('pip')
    conda = Command('conda')
    docker = Command('docker')
    docker_machine = Command('docker-machine')

    def __getattr__(self, name):
        if name not in self._commands:
            raise AttributeError(name)
        name = name.replace('_', '-')
        return Command(name).bind(self)

    def add_command(self, name):
        self._commands.add(name)

    def prepare(self, *args, **kwargs):
        return _PreparedCommand(cmd=cmd(*args, **kwargs), shell=self.shell.clone())

    def command(self, args):
        return _PreparedCommand(args, shell=self.shell.clone())

    def in_docker_machine(self, machine):
        new_shell = self.shell.clone()
        output, _ignored = self.docker_machine.env(machine, shell='cmd').batch()
        for line in output.splitlines():
            directive, args = line.split(None, 1)
            if directive != 'SET':
                continue
            key, value = args.split('=', 1)
            new_shell.setenv(key, value)
        return attr.assoc(self, shell=new_shell)

    def pip_install(self, pkg_ids, index_url=NO_VALUE):
        if index_url is NO_VALUE:
            index_url = self.pypi 
        # TODO: should index_url be extra_index_url etc.
        if index_url:
            trusted_host = urlparse.urlparse(index_url).netloc
            kwargs = dict(extra_index_url=index_url, trusted_host=trusted_host)
        else:
            kwargs = {}
        cmd = self.pip.install(*pkg_ids, **kwargs)
        return cmd.batch()

    def conda_install(self, pkg_ids, channels=None):
        cmd = self.conda.install(quiet=NO_VALUE, yes=NO_VALUE, show_channel_urls=NO_VALUE,
                                 channel=(channels or []), *pkg_ids)
        return cmd.batch()

## SK_PYPI_URL = 'http://pypi.shopkick.com/mirror'
