#!/usr/bin/env python
import io
import os
import re

from setuptools import setup


def _read_text_file(file_name):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    with io.open(file_path, encoding='utf-8') as f_stream:
        return f_stream.read()


def _get_version():
    return re.search("__version__\s*=\s*'([^']+)'\s*",
                     _read_text_file('pytest_catchlog.py')).group(1)


setup(name='pytest-catchlog',
      version=_get_version(),
      description=('py.test plugin to catch log messages.'
                   ' This is a fork of pytest-capturelog.'),
      long_description=_read_text_file('README.rst'),
      author='Arthur Skowronek (Fork Author)',  # original author: Meme Dough
      author_email='eisensheng@mailbox.org',
      url='https://github.com/eisensheng/pytest-catchlog',
      py_modules=['pytest_catchlog', ],
      install_requires=['py>=1.1.1', ],
      entry_points={'pytest11': ['pytest_catchlog = pytest_catchlog']},
      license='MIT License',
      zip_safe=False,
      keywords='py.test pytest',
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.2',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: Implementation :: CPython',
                   'Programming Language :: Python :: Implementation :: PyPy',
                   'Topic :: Software Development :: Testing'])
