import unittest

import attr

from seashore import executor

@attr.s
class DummyShell(object):

    _env = attr.ib(default=attr.Factory(dict))

    def clone(self):
        return attr.assoc(self, _env=dict(self._env))

    def batch(self, *args, **kwargs):
        if args == ('docker-machine env --shell cmd confluent'.split(),) and kwargs == {}:
            return ('SET DOCKER_TLS_VERIFY=1\n'
                    'SET DOCKER_HOST=tcp://192.168.99.103:2376\n'
                    'SET DOCKER_CERT_PATH=/Users/moshezadka/.docker/machine/machines/confluent\n'
                    'SET DOCKER_MACHINE_NAME=confluent\n'
                    'REM Run this command to configure your shell: \n'
                    'REM 	@FOR /f "tokens=*" %i IN (\'docker-machine env --shell cmd confluent\') '
                    'DO @%i\n')
        raise ValueError(args, kwargs)

class ExecutorTest(unittest.TestCase):

    def setUp(self):
        self.shell = DummyShell()
        self.executor = executor.Executor(self.shell)

    def test_in_docker_machine(self):
        new_executor = self.executor.in_docker_machine('confluent')
        new_executor.docker.run('a-machine:a-tag', remove=executor.NO_VALUE, interactive=executor.NO_VALUE,
                                terminal=executor.NO_VALUE)
        raise ValueError(self.shell)
