from __future__ import absolute_import, division, print_function

import setuptools

setuptools.setup(
    name='seashore',
    maintainer='Moshe Zadka',
    maintainer_email='moshe@shopkick.com',
    url="http://gitlab.internal.shopkick.com/shopkick/seashore",
    use_incremental=True,
    setup_requires=['incremental'],
    install_requires=[
        'incremental',
        'attrs',
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages('src'),
    description='Stuff',
    long_description='More stff',
)
