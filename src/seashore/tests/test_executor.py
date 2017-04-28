import unittest

import attr

from seashore import executor

@attr.s
class DummyShell(object):

    _env = attr.ib(default=attr.Factory(dict))

    def clone(self):
        return attr.assoc(self, _env=dict(self._env))

    def setenv(self, key, value):
        self._env[key] = value

    def batch(self, *args, **kwargs):
        if args == ('docker-machine env --shell cmd confluent'.split(),) and kwargs == {}:
            return ('SET DOCKER_TLS_VERIFY=1\n'
                    'SET DOCKER_HOST=tcp://192.168.99.103:2376\n'
                    'SET DOCKER_CERT_PATH=/Users/moshezadka/.docker/machine/machines/confluent\n'
                    'SET DOCKER_MACHINE_NAME=confluent\n'
                    'REM Run this command to configure your shell: \n'
                    'REM 	@FOR /f "tokens=*" %i IN (\'docker-machine env --shell cmd confluent\') '
                    'DO @%i\n', '')
        if (len(args) == 1 and args[0][:2] == 'docker run'.split() and
            set(args[0][2:-1]) == set('--interactive --remove --terminal'.split()) and
            args[0][-1] =='a-machine:a-tag' and
            self._env['DOCKER_MACHINE_NAME'] == 'confluent' and
            self._env['DOCKER_CERT_PATH'] == '/Users/moshezadka/.docker/machine/machines/confluent' and
            self._env['DOCKER_TLS_VERIFY'] ==  '1' and
            self._env['DOCKER_HOST'] == 'tcp://192.168.99.103:2376'):
            return 'hello\r\n', ''
        if args == ('pip install attrs'.split(),):
            return 'attrs installed', ''
        if args == ('apt-get update'.split(),):
            return 'update finished successfully', ''
        if args == ('echo hello'.split(),):
            return 'hello\n', ''
        if (len(args) == 1 and args[0][:2] == 'pip install'.split() and
            args[0][-1] =='attrs' and
            '--trusted-host' in args[0] and
            args[0][args[0].index('--trusted-host')+1] == 'orbifold.xyz' and
            '--extra-index-url' in args[0] and
            args[0][args[0].index('--extra-index-url')+1] == 'http://orbifold.xyz'):
            return 'attrs installed from orbifold', ''
        if (len(args) == 1 and args[0][:2] == 'conda install'.split() and
            set(args[0][2:-1]) == set('--show-channel-urls --quiet --yes'.split()) and
            args[0][-1] =='numpy'):
            return 'numpy installed', ''
        raise ValueError(self, args, kwargs)

    def interactive(self, *args, **kwargs):
        if args == (['python'],):
            return
        raise ValueError(self, args, kwargs)

    def popen(self, *args, **kwargs):
        if args == (['grep', 'foo'],):
            return
        raise ValueError(self, args, kwargs)


class ExecutorTest(unittest.TestCase):

    def setUp(self):
        self.shell = DummyShell()
        self.executor = executor.Executor(self.shell)

    def test_in_docker_machine(self):
        new_executor = self.executor.in_docker_machine('confluent')
        output, err = new_executor.docker.run('a-machine:a-tag', remove=executor.NO_VALUE,
                                              interactive=executor.NO_VALUE,
                                              terminal=executor.NO_VALUE).batch()
        self.assertEquals(output,'hello\r\n')

    def test_call(self):
        output, error = self.executor.pip('install', 'attrs').batch()
        self.assertEquals(output, 'attrs installed')

    def test_arbitrary(self):
        self.executor.add_command('apt_get')
        output, error = self.executor.apt_get.update().batch()
        self.assertEquals(output, 'update finished successfully')

    def test_command(self):
        output, error = self.executor.command(['echo', 'hello']).batch()
        self.assertEquals(output, 'hello\n')

    def test_pip_install(self):
        output, error = self.executor.pip_install(['attrs'])
        self.assertEquals(output, 'attrs installed')

    def test_pip_install_index(self):
        output, error = self.executor.pip_install(['attrs'], index_url='http://orbifold.xyz')
        self.assertEquals(output, 'attrs installed from orbifold')

    def test_conda_install(self):
        output, error = self.executor.conda_install(['numpy'])
        self.assertEquals(output, 'numpy installed')

    def test_interactive(self):
        self.executor.command(['python']).interactive()

    def test_popen(self):
        proc = self.executor.command(['grep', 'foo']).popen()
