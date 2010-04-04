"""py.test plugin to capture log messages"""

import py

def pytest_addoption(parser):
    """Add options to control log capturing."""

    group = parser.getgroup('general')
    group.addoption('--nocapturelog',
                    dest='capturelog',
                    action='store_false',
                    default=True,
                    help='disable log capture')

def pytest_configure(config):
    """Activate log capturing if appropriate."""

    if config.getvalue('capturelog'):
        config.pluginmanager.register(Capturer(), 'capturelog')

class Capturer(object):
    """Attaches to the logging module and captures log messages for each test."""

    def __init__(self):
        """Create a new capturer.

        Establish a handler that collects all log messages from the
        root logger.
        """

        # Import here so that we only import if we are going to capture.
        import logging

        # Create a logging handler for the entire test session.
        self.stream = py.io.TextIO()
        self.formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setFormatter(self.formatter)

        # Attach the logging handler to the root logger.
        self.logger = logging.getLogger()
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.NOTSET)

    def pytest_runtest_setup(self, item):
        """Start capturing log messages for this test.

        The handler is directed to put all log messages into the
        stream for this specific test.
        """

        item.capturelog_stream = py.io.TextIO()
        self.handler.stream = item.capturelog_stream

    def pytest_runtest_teardown(self, item):
        """Stop capturing log messages for this test.

        The handler is directed to put any log messages that occur
        outside of a test into the stream owned by the capturer.
        """

        self.handler.stream = self.stream
        item.capturelog_stream.close()
        del item.capturelog_stream

    def pytest_runtest_makereport(self, __multicall__, item, call):
        """Add captured log messages for this report."""

        report = __multicall__.execute()

        # This fn called after setup, call and teardown.  Only
        # interested in just after test call has finished.
        if call.when == 'call':

            # For failed tests that have captured log messages add a
            # captured log section to the report.
            if not report.passed:
                longrepr = getattr(report, 'longrepr', None)
                if hasattr(longrepr, 'addsection'):
                    log = item.capturelog_stream.getvalue().strip()
                    if log:
                        longrepr.addsection('Captured log', log)

        return report

    def pytest_terminal_summary(self, terminalreporter):
        """Report any log messages that occurred outside of tests."""

        log = self.stream.getvalue().strip()
        if log:
            tw = terminalreporter._tw
            tw.sep('-', 'Session captured log (occurred outside of any test)')
            tw.write(log)
            tw.write('\n')
