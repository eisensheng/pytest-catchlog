from __future__ import absolute_import, division, print_function

import logging


logger = logging.getLogger('pytest_catchlog.test.perf')


def test_log_emit(benchmark):
    benchmark(logger.info, 'Testing %s performance: %s',
              'catchlog', 'emit a single log record')
