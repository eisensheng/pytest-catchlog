# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import pytest


pytest_plugins = 'pytester'


def pytest_addoption(parser):
    parser.addoption('--run-perf',
        action='store', dest='run_perf',
        choices=['yes', 'no', 'only', 'check'],
        nargs='?', default='check', const='yes',
        help='Run performance tests (can be slow)',
    )
