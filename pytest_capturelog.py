"""capture output of logging module.

Installation
------------

You can install the `pytest-capturelog pypi`_ package
with pip::

    pip install pytest-capturelog

or with easy install::

    easy_install pytest-capturelog

.. _`pytest-capturelog pypi`: http://pypi.python.org/pypi/pytest-capturelog/

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


Inside tests it is possible to change the loglevel for the captured
log messages.  This is supported by the ``capturelog`` funcarg::

    def test_foo(capturelog):
        capturelog.setLevel(logging.INFO)
        pass

It is also possible to use the capturelog as a context manager to
temporarily change the log level::

    def test_bar(capturelog):
        with capturelog(logging.INFO):
            pass

Lastly the LogRecord instances sent to the logger during the test run
are also available on the function argument.  This is useful for when
you want to assert on the contents of a message::

    def test_baz(capturelog):
        func_under_test()
        for record in capturelog.raw_records:
            assert record.levelname != 'CRITICAL'

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
        config.pluginmanager.register(Capturer(config), '_capturelog')


class CapturelogHandler(logging.StreamHandler):
    def __call__(self, level):
        self.__tmp_level = level
        return self

    def __enter__(self):
        self.__enter_level = self.level
        self.level = self.__tmp_level
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.level = self.__enter_level

    def emit(self, record):
        """Keep the raw records in a buffer as well"""
        try:
            self.raw_records.append(record)
        except AttributeError:
            self.raw_records = [record]
        logging.StreamHandler.emit(self, record)


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
        item.capturelog_handler = CapturelogHandler(item.capturelog_stream)
        item.capturelog_handler.setFormatter(self.formatter)
        item.function.capturelog_handler = item.capturelog_handler
        item.capturelog_loglevel = logging.getLogger().level

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

            # Restore loglevel
            root_logger.setLevel(item.capturelog_loglevel)

        return report

    def pytest_funcarg__capturelog(self, request):
        """Returns the log handler configured for this logger

        This can be used to modify the loglevel or format inside a
        test.
        """
        return request.function.capturelog_handler
