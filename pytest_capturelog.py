"""py.test plugin to capture log messages"""

import py
import logging

def pytest_addoption(parser):
    """Adds options to py.test for controlling log capturing."""

    group = parser.getgroup('general')
    group.addoption('--nocapturelog',
                    dest='capturelog',
                    action='store_false',
                    default=True,
                    help='disable log capture')


def pytest_runtest_setup(item):
    """Start capturing log messages for this test."""

    if item.config.getvalue('capturelog'):

        # Create a logging handler for this test.
        item.capturelog_stream = py.io.TextIO()
        item.capturelog_handler = logging.StreamHandler(item.capturelog_stream)
        item.capturelog_formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')
        item.capturelog_handler.setFormatter(item.capturelog_formatter)

        # Attach the logging handler to the root logger.
        root_logger = logging.getLogger()
        root_logger.addHandler(item.capturelog_handler)
        root_logger.setLevel(logging.NOTSET)


def pytest_runtest_teardown(item):
    """Stop capturing log messages for this test."""

    if item.config.getvalue('capturelog'):

        # Detach the logging handler from the root logger.
        logging.getLogger().removeHandler(item.capturelog_handler)


def pytest_runtest_makereport(__multicall__, item, call):
    """Add captured log messages for this report."""

    report = __multicall__.execute()

    if item.config.getvalue('capturelog'):

        # For failed tests that have captured log messages add a
        # captured log section to the report.
        if not report.passed:
            longrepr = getattr(report, 'longrepr', None)
            if hasattr(longrepr, 'addsection'):
                log = item.capturelog_stream.getvalue()
                if log:
                    longrepr.addsection('Captured log', log)

    return report
