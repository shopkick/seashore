#!/usr/bin/python
if __name__ != "__main__":
    raise ImportError()


import subprocess
import os
import os.path


docker_ctx = os.path.dirname(os.path.abspath(__file__))
tag = 'seashore-test-' + os.environ['CI_JOB_ID']
dst = docker_ctx + '/repo'
src = os.environ['CI_PROJECT_DIR']
os.mkdir(dst)
subprocess.check_call(['cp', '-r', src + '/src', dst])
subprocess.check_call(['cp', '-r', src + '/tox.ini', dst])
subprocess.check_call(['docker', 'build', '-t', tag, '.'])
subprocess.check_call(['docker', 'rmi', tag])

