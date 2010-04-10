"""py.test plugin to capture log messages"""

import py
import logging

def pytest_addoption(parser):
    """Add options to control log capturing."""

    group = parser.getgroup('capturelog', 'log capturing')
    group.addoption('--nocapturelog',
                    dest='capturelog',
                    action='store_false',
                    default=True,
                    help='disable log capture')
    group.addoption('--log-format',
                    dest='log_format',
                    default='%(filename)-25s %(lineno)4d %(levelname)-8s %(message)s',
                    help='log format as used by the logging module')
    group.addoption('--log-date-format',
                    dest='log_date_format',
                    default=None,
                    help='log date format as used by the logging module')

def pytest_configure(config):
    """Activate log capturing if appropriate."""

    if config.getvalue('capturelog'):
        config.pluginmanager.register(Capturer(config), 'capturelog')

class Capturer(object):
    """Attaches to the logging module and captures log messages for each test."""

    def __init__(self, config):
        """Creates a new capturer.

        The formatter can be safely shared across all handlers so
        create a single one for the entire test session here.
        """

        self.formatter = logging.Formatter(config.getvalue('log_format'),
                                           config.getvalue('log_date_format'))

    def pytest_runtest_setup(self, item):
        """Start capturing log messages for this test.

        Creating a specific handler and stream for each test ensures
        that we avoid multi threading issues.

        Attaching the handler and setting the level at the beginning
        of each test ensures that we are setup to capture log
        messages.
        """

        # Create a handler and stream for this test.
        item.capturelog_stream = py.io.TextIO()
        item.capturelog_handler = logging.StreamHandler(item.capturelog_stream)
        item.capturelog_handler.setFormatter(self.formatter)

        # Attach the handler to the root logger and ensure that the
        # root logger is set to log all levels.
        root_logger = logging.getLogger()
        root_logger.addHandler(item.capturelog_handler)
        root_logger.setLevel(logging.NOTSET)

    def pytest_runtest_makereport(self, __multicall__, item, call):
        """Add captured log messages for this report."""

        report = __multicall__.execute()

        # This fn called after setup, call and teardown.  Only
        # interested in just after test call has finished.
        if call.when == 'call':

            # Detach the handler from the root logger to ensure no
            # further access to the handler and stream.
            root_logger = logging.getLogger()
            root_logger.removeHandler(item.capturelog_handler)

            # For failed tests that have captured log messages add a
            # captured log section to the report.
            if not report.passed:
                longrepr = getattr(report, 'longrepr', None)
                if hasattr(longrepr, 'addsection'):
                    log = item.capturelog_stream.getvalue().strip()
                    if log:
                        longrepr.addsection('Captured log', log)

            # Release the handler and stream resources.
            item.capturelog_handler.close()
            item.capturelog_stream.close()
            del item.capturelog_handler
            del item.capturelog_stream

        return report
