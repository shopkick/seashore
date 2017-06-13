.. Copyright (c) Shopkick
   See LICENSE for details.

Seashore
========

.. toctree::
   :maxdepth: 2

Quick start
-----------

The Seashore library enables Pythonic command-based automation.

Creating an executor is easy:

.. code::

    from seashore import Executor, Shell, NO_VALUE
    xctor = seashore.Executor(seashore.Shell())

Running commands looks like calling Python functions.
In batch mode, commands will return their standard output and error.

.. code::

    base, dummy = xctr.git.rev_parse(show_toplevel=seashore.NO_VALUE,
                                    ).batch(cwd=git_dir)

If an error occurs, an exception will be raised.
If we just want to exit if any error is raised, but not leave a traceback,

.. code::

    def main():
         with seashore.autocode_exit():
            call_functions()
            run_executors()

The context will auto translate process errors to system exit. 

There are also nice helpers, like :code:`in_docker_machine`,
which will return an executor where the docker commands are all pointed
at a given docker machine.

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

Release Process
---------------

In a virtual environment:

.. code::

    $ pip install incremental twisted click twine
    $ git checkout master
    $ git pull --rebase
    $ git checkout -b new-release
    $ python -m incremental.update --patch
    $ git commit -a -m 'update to new version'
    $ git push

On GitHub, create Pull Request, review and merge.

Then, back in the virtual environment:

.. code::

    $ git checkout master
    $ git pull --rebase
    $ pip wheel .
    $ python setup.py sdist
    $ twine upload seashore*.whl dist/seashore*.tar.gz
    $ git tag v<version number>
    $ git push --tags

On GitHub, create a release. Names for next few releases:

* Dimorphodon macronyx
* Squaloraja polyspondyla
* Coprolite

We base releases on the discoveries of `Mary Anning`_ 
who is the heroine of the tongue twister "she sells seashells by the seashore".

.. _Mary Anning: https://en.wikipedia.org/wiki/Mary_Anning

After releasing, make sure to avoid accidental releases:

.. code::

    $ git checkout master
    $ git pull --rebase
    $ git checkout -b make-dev
    $ python -m incremental.update seashore --dev
    $ git commit -a -m 'prevent accidental releases'
    $ git push

On GitHub, review and merge.
