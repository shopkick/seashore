.. Copyright (c) Shopkick
   See LICENSE for details.

Seashore
========

.. toctree::
   :maxdepth: 2

Quick start
-----------

Blah blah 

.. code::

    from seashore import Executor, Shell, NO_VALUE
    xctor = seashore.Executor(seashore.Shell())

Blah blah 

.. code::

    base, dummy = xctr.git.rev_parse(show_toplevel=seashore.NO_VALUE).batch(cwd=git_dir)

Blah blah 

.. code::

    dock_xctr = xctr.in_docker_machine('default')
    dock_xctr.docker.run('ubuntu:latest', net='none',
                         rm=seashore.NO_VALUE,
                         interactive=seashore.NO_VALUE,
                         terminal=seashore.NO_VALUE,
                         volume='/myvolume',
                         env=dict(AWESOME='TRUE')).interactive()



API
---

.. automodule:: seashore.executor
   :members:

.. automodule:: seashore.shell
   :members:
