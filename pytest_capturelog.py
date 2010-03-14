"""py.test plugin to capture log messages"""

import py
import logging

def pytest_addoption(parser):
    group = parser.getgroup('general')
    group.addoption('--nocapturelog',
                    dest='capturelog',
                    action='store_false',
                    default=True,
                    help='disable log capture')


def pytest_runtest_setup(item):
    if item.config.getvalue('capturelog'):
        item.capturelog_stream = py.io.TextIO()
        item.capturelog_handler = logging.StreamHandler(item.capturelog_stream)
        item.capturelog_formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')
        item.capturelog_handler.setFormatter(item.capturelog_formatter)
        root_logger = logging.getLogger()
        root_logger.addHandler(item.capturelog_handler)
        root_logger.setLevel(logging.NOTSET)


def pytest_runtest_teardown(item):
    if item.config.getvalue('capturelog'):
        logging.getLogger().removeHandler(item.capturelog_handler)


def pytest_runtest_makereport(__multicall__, item, call):
    report = __multicall__.execute()

    if item.config.getvalue('capturelog'):
        if not report.passed:
            longrepr = getattr(report, 'longrepr', None)
            if hasattr(longrepr, 'addsection'):
                log = item.capturelog_stream.getvalue()
                if log:
                    longrepr.addsection('Captured log', log)

    return report
