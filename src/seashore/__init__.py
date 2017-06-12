# Copyright (c) Shopkick 2017
# See LICENSE for details.
"""
Seashore
=======

Seashore is a collection of shell abstractions.
"""
from seashore.executor import Executor, NO_VALUE, Eq
from seashore.shell import Shell, ProcessError
from seashore._version import __version__

__all__ = ['Executor', 'NO_VALUE', 'Eq', 'Shell', 'ProcessError', '__version__']
