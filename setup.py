# -*- coding: utf-8 -*-
#
# This software may be modified and distributed under the terms
# of the Apache License, Version 2.0 license.  See the LICENSE file for details.

from os import path
from shutil import rmtree
import sys

from setuptools import setup


NAME = 'pylogbeat'
VERSION = '2.0.0'

here = path.abspath(path. dirname(__file__))
with open(path.join(here, 'README.md'), 'rb') as f:
    LONG_DESCRIPTION = f.read().decode('utf-8')


if 'bdist_wheel' in sys.argv:
    for directory in ('build', 'dist', 'pylogbeat.egg-info'):
        rmtree(directory, ignore_errors=True)  # cleanup


setup(
    name=NAME,
    py_modules=['pylogbeat'],
    version=VERSION,
    description='Simple, incomplete implementation of the Beats protocol '
                'used by Elastic Beats and Logstash.',
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    license='Apache License 2.0',
    author='Enrico Tröger',
    author_email='enrico.troeger@uvena.de',
    url='https://github.com/eht16/pylogbeat/',
    project_urls={
        'Travis CI': 'https://travis-ci.org/eht16/pylogbeat/',
        'Source code': 'https://github.com/eht16/pylogbeat/',
    },
    keywords='logging logstash beats',
    python_requires='>3.6',
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Logging',
    ]
)
