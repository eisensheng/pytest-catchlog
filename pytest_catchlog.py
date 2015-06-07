# -*- coding: utf-8 -*-
from __future__ import (absolute_import, print_function,
                        unicode_literals, division)

import logging

import py


__version__ = '1.1'


def pytest_addoption(parser):
    """Add options to control log capturing."""

    group = parser.getgroup('catchlog', 'Log catching.')
    group.addoption('--no-print-logs',
                    dest='log_print', action='store_false', default=True,
                    help='disable printing caught logs on failed tests.')
    group.addoption('--log-format',
                    dest='log_format',
                    default=('%(filename)-25s %(lineno)4d'
                             ' %(levelname)-8s %(message)s'),
                    help='log format as used by the logging module.')
    group.addoption('--log-date-format',
                    dest='log_date_format', default=None,
                    help='log date format as used by the logging module.')


def pytest_configure(config):
    """Always register the log catcher plugin with py.test or tests can't
    find the  fixture function.
    """
    config.pluginmanager.register(CatchLogPlugin(config), '_catch_log')


class CatchLogPlugin(object):
    """Attaches to the logging module and captures log messages for each test.
    """

    def __init__(self, config):
        """Creates a new plugin to capture log messages.

        The formatter can be safely shared across all handlers so
        create a single one for the entire test session here.
        """
        self.print_logs = config.getvalue('log_print')
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
        item.catch_log_handler = CatchLogHandler()
        item.catch_log_handler.setFormatter(self.formatter)

        # Attach the handler to the root logger and ensure that the
        # root logger is set to log all levels.
        root_logger = logging.getLogger()
        root_logger.addHandler(item.catch_log_handler)
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
            root_logger.removeHandler(item.catch_log_handler)

            # For failed tests that have captured log messages add a
            # captured log section to the report if desired.
            if not report.passed and self.print_logs:
                long_repr = getattr(report, 'longrepr', None)
                if hasattr(long_repr, 'addsection'):
                    log = item.catch_log_handler.stream.getvalue().strip()
                    if log:
                        long_repr.addsection('Captured log', log)

            # Release the handler resources.
            item.catch_log_handler.close()
            del item.catch_log_handler

        return report


class CatchLogHandler(logging.StreamHandler):
    """A logging handler that stores log records and the log text."""

    def __init__(self):
        """Creates a new log handler."""

        logging.StreamHandler.__init__(self)
        self.stream = py.io.TextIO()
        self.records = []

    def close(self):
        """Close this log handler and its underlying stream."""

        logging.StreamHandler.close(self)
        self.stream.close()

    def emit(self, record):
        """Keep the log records in a list in addition to the log text."""

        self.records.append(record)
        logging.StreamHandler.emit(self, record)


class CatchLogFuncArg(object):
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

    def record_tuples(self):
        """Returns a list of a striped down version of log records intended
        for use in assertion comparison.

        The format of the tuple is:

            (logger_name, log_level, message)
        """
        return [(r.name, r.levelno, r.getMessage()) for r in self.records()]

    def set_level(self, level, logger=None):
        """Sets the level for capturing of logs.

        By default, the level is set on the handler used to capture
        logs. Specify a logger name to instead set the level of any
        logger.
        """

        obj = logger and logging.getLogger(logger) or self.handler
        obj.setLevel(level)

    def at_level(self, level, logger=None):
        """Context manager that sets the level for capturing of logs.

        By default, the level is set on the handler used to capture
        logs. Specify a logger name to instead set the level of any
        logger.
        """

        obj = logger and logging.getLogger(logger) or self.handler
        return CatchLogLevel(obj, level)


class CatchLogLevel(object):
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

    return CatchLogFuncArg(request._pyfuncitem.catch_log_handler)


def pytest_funcarg__capturelog(request):
    """Returns a funcarg to access and control log capturing."""

    return CatchLogFuncArg(request._pyfuncitem.catch_log_handler)
