#!/usr/bin/python
if __name__ != "__main__":
    raise ImportError()


import subprocess
import os


tag = 'seashore-test-' + os.environ['CI_JOB_ID']
subprocess.check_call(['cp', '-r', os.environ['CI_PROJECT_DIR'], '.'])
subprocess.check_call(['docker', 'build', '-t', tag, '.'])
subprocess.check_call(['docker', 'rmi', tag])

