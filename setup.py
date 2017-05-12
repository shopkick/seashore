# Copyright (c) Shopkick 2017
# See LICENSE for details.
from __future__ import absolute_import, division, print_function

import setuptools

with open('README.rst') as fp:
    long_description = fp.read()

setuptools.setup(
    name='seashore',
    maintainer='Shopkick',
    maintainer_email='dev@shopkick.com',
    url="http://github.com/shopkick/seashore",
    use_incremental=True,
    setup_requires=['incremental'],
    license='MIT',
    install_requires=[
        'incremental',
        'attrs',
        'singledispatch',
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages('src'),
    description='A collection of shell abstractions',
    long_description=long_description,
)
