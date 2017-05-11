# Copyright (c) Shopkick
# See LICENSE for details.
import os
import sys

up = os.path.dirname(os.path.dirname(__file__))
sys.path.append(up)

import seashore

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]
master_doc = 'index'
project = 'Seashore'
copyright = '2017, Shopkick'
author = 'Shopkick'
version = release = str(seashore.__version__)
