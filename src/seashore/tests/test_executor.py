# Copyright (c) Shopkick 2017
# See LICENSE for details.
# pragma pylint: disable=too-many-boolean-expressions
# pragma pylint: disable=too-many-return-statements
"""Test seashore.executor"""

import unittest

import attr

from seashore import executor

@attr.s
class DummyShell(object):

    """Dummy Shell"""

    _env = attr.ib(default=attr.Factory(dict))

    def clone(self):
        """Return a copy of the shell"""
        return attr.assoc(self, _env=dict(self._env))

    def setenv(self, key, value):
        """Set an environment variable"""
        self._env[key] = value

    def getenv(self, key):
        """Get an environment variable"""
        return self._env[key]

    def batch(self, *args, **kwargs):
        """(Pretend to) run a command in batch mode"""
        if args == ('docker-machine env --shell cmd confluent'.split(),) and kwargs == {}:
            return ('SET DOCKER_TLS_VERIFY=1\n'
                    'SET DOCKER_HOST=tcp://192.168.99.103:2376\n'
                    'SET DOCKER_CERT_PATH=/Users/u/.docker/machine/machines/confluent\n'
                    'SET DOCKER_MACHINE_NAME=confluent\n'
                    'REM Run this command to configure your shell: \n'
                    'REM 	@FOR /f "tokens=*" %i IN (\'docker-machine env --shell cmd confluent\') '
                    'DO @%i\n', '')
        if (len(args) == 1 and args[0][:2] == 'docker run'.split() and
                set(args[0][2:-1]) == set('--interactive --remove --terminal'.split()) and
                args[0][-1] == 'a-machine:a-tag' and
                self._env['DOCKER_MACHINE_NAME'] == 'confluent' and
                self._env['DOCKER_CERT_PATH'] == '/Users/u/.docker/machine/machines/confluent' and
                self._env['DOCKER_TLS_VERIFY'] == '1' and
                self._env['DOCKER_HOST'] == 'tcp://192.168.99.103:2376'):
            return 'hello\r\n', ''
        if args == ('pip install attrs'.split(),):
            return 'attrs installed', ''
        if (args == ('pip install a-local-package'.split(),) and
                self._env['VIRTUAL_ENV'] == '/appenv'):
            return 'a-local-package installed', ''
        if args == ('apt-get update'.split(),):
            return 'update finished successfully', ''
        if args == ('echo hello'.split(),):
            return 'hello\n', ''
        if (len(args) == 1 and args[0][:2] == 'pip install'.split() and
                args[0][-1] == 'attrs' and
                '--trusted-host' in args[0] and
                args[0][args[0].index('--trusted-host')+1] == 'orbifold.xyz' and
                '--extra-index-url' in args[0] and
                args[0][args[0].index('--extra-index-url')+1] == 'http://orbifold.xyz'):
            return 'attrs installed from orbifold', ''
        if (len(args) == 1 and args[0][:2] == 'conda install'.split() and
                set(args[0][2:-1]) == set('--show-channel-urls --quiet --yes'.split()) and
                args[0][-1] == 'numpy'):
            return 'numpy installed', ''
        if (len(args) == 1 and args[0][:2] == 'docker run'.split() and
                args[0][2] == '--env' and
                args[0][4] == '--env' and
                set([args[0][3], args[0][5]]) == set(['SONG=awesome', 'SPECIAL=emett']) and
                args[0][-1] == 'lego:1'):
            return 'everything', ''
        if args == ('do-stuff special --verbosity 5'.split(),):
            return 'doing stuff very specially', ''
        if (len(args) == 1 and args[0][:2] == 'chat mention'.split() and
                args[0][2] == '--person' and
                args[0][4] == '--person' and
                set([args[0][3], args[0][5]]) == set(['emett', 'lucy'])):
            return 'mentioning folks', ''
        raise ValueError(self, args, kwargs)

    def interactive(self, *args, **kwargs):
        """(Pretend to) run a command in interactive mode"""
        if args == (['python'],):
            return
        raise ValueError(self, args, kwargs)

    def popen(self, *args, **kwargs):
        """(Pretend to) run a command in popen mode"""
        if args == (['grep', 'foo'],):
            return
        raise ValueError(self, args, kwargs)


class ExecutorTest(unittest.TestCase):

    """Test Executor"""

    def setUp(self):
        """build an executor with a dummy shell"""
        self.shell = DummyShell()
        self.executor = executor.Executor(self.shell)

    def test_in_docker_machine(self):
        """calling in_docker_machine returns an executor that runs docker pointed at the machine"""
        new_executor = self.executor.in_docker_machine('confluent')
        output, _err = new_executor.docker.run('a-machine:a-tag', remove=executor.NO_VALUE,
                                               interactive=executor.NO_VALUE,
                                               terminal=executor.NO_VALUE).batch()
        self.assertEquals(output, 'hello\r\n')

    def test_in_virtualenv(self):
        """calling in_virtualenv returns an executor that runs pip in a virtual env"""
        new_executor = self.executor.in_virtualenv('/appenv')
        output, _err = new_executor.pip.install('a-local-package').batch()
        self.assertEquals(output, 'a-local-package installed')
        new_executor_one = self.executor.patch_env(PATH='/bin')
        new_executor_two = new_executor_one.in_virtualenv('/appenv')
        output, _err = new_executor_two.pip.install('a-local-package').batch()
        self.assertEquals(output, 'a-local-package installed')

    def test_call(self):
        """calling a built-in command runs it in the shell"""
        output, _error = self.executor.pip('install', 'attrs').batch()
        self.assertEquals(output, 'attrs installed')

    def test_arbitrary(self):
        """adding an arbitrary command allows access via attribute"""
        self.executor.add_command('apt_get')
        output, _error = self.executor.apt_get.update().batch()
        self.assertEquals(output, 'update finished successfully')

    def test_command(self):
        """using the command method passes the arguments directly to the shell"""
        output, _error = self.executor.command(['echo', 'hello']).batch()
        self.assertEquals(output, 'hello\n')

    def test_pip_install(self):
        """calling pip_install() runs 'pip install'"""
        output, _error = self.executor.pip_install(['attrs'])
        self.assertEquals(output, 'attrs installed')

    def test_pip_install_index(self):
        """passing the index_url param to pip_install passes it to the pip install command"""
        output, _error = self.executor.pip_install(['attrs'], index_url='http://orbifold.xyz')
        self.assertEquals(output, 'attrs installed from orbifold')

    def test_conda_install(self):
        """the conda_install() method calls 'conda install'"""
        output, _error = self.executor.conda_install(['numpy'])
        self.assertEquals(output, 'numpy installed')

    def test_interactive(self):
        """interactive mode does not fail"""
        self.executor.command(['python']).interactive()

    def test_non_existant_command(self):
        """non-existing commands raise AttributeError"""
        with self.assertRaises(AttributeError):
            self.executor.this_command_doesnt_exist.install().batch()

    def test_popen(self):
        """popen does not fail"""
        self.executor.command(['grep', 'foo']).popen()

    def test_dict_keywords(self):
        """prepare with dict value explodes the dict"""
        output, _err = self.executor.docker.run('lego:1', env=dict(SPECIAL='emett',
                                                                   SONG='awesome')).batch()
        self.assertEquals(output, 'everything')

    def test_int(self):
        """prepare with int option stringifies the int"""
        output, _err = self.executor.prepare('do-stuff', 'special', verbosity=5).batch()
        self.assertEquals(output, 'doing stuff very specially')

    def test_list(self):
        """prepare with list option explodes into a list of options"""
        output, _err = self.executor.prepare('chat', 'mention', person=['emett', 'lucy']).batch()
        self.assertEquals(output, 'mentioning folks')
