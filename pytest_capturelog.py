"""capture output of logging module.

Installation
------------

The `pytest-capturelog`_ package may be installed with pip or easy_install::

    pip install pytest-capturelog
    easy_install pytest-capturelog

.. _`pytest-capturelog`: http://pypi.python.org/pypi/pytest-capturelog/

Usage
-----

If the plugin is installed log messages are captured by default and for
each failed test will be shown in the same manner as captured stdout and
stderr.

Running without options::

    py.test test_capturelog.py

Shows failed tests like so::

    -------------------------- Captured log ---------------------------
    test_capturelog.py          26 INFO     text going to logger
    ------------------------- Captured stdout -------------------------
    text going to stdout
    ------------------------- Captured stderr -------------------------
    text going to stderr
    ==================== 2 failed in 0.02 seconds =====================

By default each captured log message shows the module, line number,
log level and message.  Showing the exact module and line number is
useful for testing and debugging.  If desired the log format and date
format can be specified to anything that the logging module supports.

Running pytest specifying formatting options::

    py.test --log-format="%(asctime)s %(levelname)s %(message)s" --log-date-format="%Y-%m-%d %H:%M:%S" test_capturelog.py

Shows failed tests like so::

    -------------------------- Captured log ---------------------------
    2010-04-10 14:48:44 INFO text going to logger
    ------------------------- Captured stdout -------------------------
    text going to stdout
    ------------------------- Captured stderr -------------------------
    text going to stderr
    ==================== 2 failed in 0.02 seconds =====================

Further it is possible to disable capturing of logs completely with::

    py.test --nocapturelog test_capturelog.py

Shows failed tests in the normal manner as no logs were captured::

    ------------------------- Captured stdout -------------------------
    text going to stdout
    ------------------------- Captured stderr -------------------------
    text going to stderr
    ==================== 2 failed in 0.02 seconds =====================

Inside tests it is possible to change the log level for the captured
log messages.  This is supported by the ``caplog`` funcarg::

    def test_foo(caplog):
        caplog.setLevel(logging.INFO)
        pass

By default the level is set on the handler used to capture the log
messages, however as a convenience it is also possible to set the log
level of any logger::

    def test_foo(caplog):
        caplog.setLevel(logging.CRITICAL, logger='root.baz')
        pass

It is also possible to use a context manager to temporarily change the
log level::

    def test_bar(caplog):
        with caplog.atLevel(logging.INFO):
            pass

Again, by default the level of the handler is affected but the level
of any logger can be changed instead with::

    def test_bar(caplog):
        with caplog.atLevel(logging.CRITICAL, logger='root.baz'):
            pass

Lastly all the logs sent to the logger during the test run are made
available on the funcarg in the form of both the LogRecord instances
and the final log text.  This is useful for when you want to assert on
the contents of a message::

    def test_baz(caplog):
        func_under_test()
        for record in caplog.records():
            assert record.levelname != 'CRITICAL'
        assert 'wally' not in caplog.text()

For all the available attributes of the log records see the
``logging.LogRecord`` class.
"""

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
        config.pluginmanager.register(CaptureLogPlugin(config), '_capturelog')


class CaptureLogPlugin(object):
    """Attaches to the logging module and captures log messages for each test."""

    def __init__(self, config):
        """Creates a new plugin to capture log messges.

        The formatter can be safely shared across all handlers so
        create a single one for the entire test session here.
        """

        self.formatter = logging.Formatter(config.getvalue('log_format'),
                                           config.getvalue('log_date_format'))

    def pytest_runtest_setup(self, item):
        """Start capturing log messages for this test.

        Creating a specific handler for each test ensures that we
        avoid multi threading issues.

        Attaching the handler and setting the level at the beginning
        of each test ensures that we are setup to capture log
        messages.
        """

        # Create a handler for this test.
        item.capturelog_handler = CaptureLogHandler()
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
            # further access to the handler.
            root_logger = logging.getLogger()
            root_logger.removeHandler(item.capturelog_handler)

            # For failed tests that have captured log messages add a
            # captured log section to the report.
            if not report.passed:
                longrepr = getattr(report, 'longrepr', None)
                if hasattr(longrepr, 'addsection'):
                    log = item.capturelog_handler.stream.getvalue().strip()
                    if log:
                        longrepr.addsection('Captured log', log)

            # Release the handler resources.
            item.capturelog_handler.close()
            del item.capturelog_handler

        return report


class CaptureLogHandler(logging.StreamHandler):
    """A logging handler that stores log records and the log text."""

    def __init__(self):
        """Creates a new log handler."""

        logging.StreamHandler.__init__(self)
        self.stream = py.io.TextIO()
        self.records  = []

    def close(self):
        """Close this log handler and its underlying stream."""

        logging.StreamHandler.close(self)
        self.stream.close()

    def emit(self, record):
        """Keep the log records in a list in addition to the log text."""

        self.records.append(record)
        logging.StreamHandler.emit(self, record)


class CaptureLogFuncArg(object):
    """Provides access and control of log capturing."""

    def __init__(self, handler):
        """Creates a new funcarg."""

        self.handler = handler

    def text(self):
        """Returns the log text."""

        return self.handler.stream.getvalue()

    def records(self):
        """Returns the list of log records."""

        return self.handler.records

    def setLevel(self, level, logger=None):
        """Sets the level for capturing of logs.

        By default, the level is set on the handler used to capture
        logs. Specify a logger name to instead set the level of any
        logger.
        """

        obj = logger and logging.getLogger(logger) or self.handler
        obj.setLevel(level)

    def atLevel(self, level, logger=None):
        """Context manager that sets the level for capturing of logs.

        By default, the level is set on the handler used to capture
        logs. Specify a logger name to instead set the level of any
        logger.
        """

        obj = logger and logging.getLogger(logger) or self.handler
        return CaptureLogLevel(obj, level)


class CaptureLogLevel(object):
    """Context manager that sets the logging level of a handler or logger."""

    def __init__(self, obj, level):
        """Creates a new log level context manager."""

        self.obj = obj
        self.level = level

    def __enter__(self):
        """Adjust the log level."""

        self.orig_level = self.obj.level
        self.obj.setLevel(self.level)

    def __exit__(self, exc_type, exc_value, traceback):
        """Restore the log level."""

        self.obj.setLevel(self.orig_level)


def pytest_funcarg__caplog(request):
    """Returns a funcarg to access and control log capturing."""

    return CaptureLogFuncArg(request._pyfuncitem.capturelog_handler)


def pytest_funcarg__capturelog(request):
    """Returns a funcarg to access and control log capturing."""

    return CaptureLogFuncArg(request._pyfuncitem.capturelog_handler)
