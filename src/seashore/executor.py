"""
Executor
--------

Construct command-line lists.

:const:`NO_VALUE` -- indicate an option with no value (a boolean option)
"""
import functools
import urlparse

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
    """
    Construct a command line for a "modern UNIX" command.

    Modern UNIX command do a closely-related-set-of-things and do it well.
    Examples include :code:`apt-get` or :code:`git`.

    :param bin: the name of the command
    :param subcommand: the subcommand used
    :param args: positional arguments (put last)
    :param kwargs: options
    :returns: list of arguments that is suitable to be passed to :code:`subprocess.Popen` and friends.

    When specifying options, the following assumptions are made:

    * Option names begin with :code:`--` and any :code:`_` is assumed to be a :code:`-`
    * If the value is :code:`NO_VALUE`, this is a "naked" option.
    * If the value is a string or an int, these are presented as the value of the option.
    * If the value is a list, the option will be repeated multiple times.
    * If the value is a dict, the option will be repeated multiple times, and
      its values will be :code:`<KEY>=<VALUE>`.
    """
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

    """
    Blah blah
    """
    name = attr.ib()

    def bind(self, executor, _dummy=None):
        """
        Blah blah
        """
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

    """
    Blah blah
    """

    _shell = attr.ib()
    pypi = attr.ib(default=None)
    _commands = attr.ib(default=attr.Factory(set), convert=set)

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
        """
        Blah blah
        """
        self._commands.add(name)

    def prepare(self, *args, **kwargs):
        """
        Blah blah
        """
        return _PreparedCommand(cmd=cmd(*args, **kwargs), shell=self.shell.clone())

    def command(self, args):
        """
        Blah blah
        """
        return _PreparedCommand(args, shell=self.shell.clone())

    def in_docker_machine(self, machine):
        """
        Blah blah
        """
        new_shell = self.shell.clone()
        output, _ignored = self.docker_machine.env(machine, shell='cmd').batch()
        for line in output.splitlines():
            directive, args = line.split(None, 1)
            if directive != 'SET':
                continue
            key, value = args.split('=', 1)
            new_shell.setenv(key, value)
        return attr.assoc(self, shell=new_shell)

    def pip_install(self, pkg_ids, index_url=None):
        """
        Blah blah
        """
        if index_url is None:
            index_url = self.pypi 
        if index_url is not None:
            trusted_host = urlparse.urlparse(index_url).netloc
            kwargs = dict(extra_index_url=index_url, trusted_host=trusted_host)
        else:
            kwargs = {}
        cmd = self.pip.install(*pkg_ids, **kwargs)
        return cmd.batch()

    def conda_install(self, pkg_ids, channels=None):
        """
        Blah blah
        """
        cmd = self.conda.install(quiet=NO_VALUE, yes=NO_VALUE, show_channel_urls=NO_VALUE,
                                 channel=(channels or []), *pkg_ids)
        return cmd.batch()
