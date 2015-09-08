pytest-catchlog
===============

py.test plugin to catch log messages.  This is a fork of `pytest-capturelog`_.

.. _`pytest-capturelog`: https://pypi.python.org/pypi/pytest-capturelog/


Installation
------------

The `pytest-catchlog`_ package may be installed with pip or easy_install::

    pip install pytest-catchlog
    easy_install pytest-catchlog

.. _`pytest-catchlog`: http://pypi.python.org/pypi/pytest-catchlog/


Usage
-----

If the plugin is installed log messages are captured by default and for
each failed test will be shown in the same manner as captured stdout and
stderr.

Running without options::

    py.test test_pytest_catchlog.py

Shows failed tests like so::

    ----------------------- Captured stdlog call ----------------------
    test_pytest_catchlog.py    26 INFO     text going to logger
    ----------------------- Captured stdout call ----------------------
    text going to stdout
    ----------------------- Captured stderr call ----------------------
    text going to stderr
    ==================== 2 failed in 0.02 seconds =====================

By default each captured log message shows the module, line number,
log level and message.  Showing the exact module and line number is
useful for testing and debugging.  If desired the log format and date
format can be specified to anything that the logging module supports.

Running pytest specifying formatting options::

    py.test --log-format="%(asctime)s %(levelname)s %(message)s" \
            --log-date-format="%Y-%m-%d %H:%M:%S" test_pytest_catchlog.py

Shows failed tests like so::

    ----------------------- Captured stdlog call ----------------------
    2010-04-10 14:48:44 INFO text going to logger
    ----------------------- Captured stdout call ----------------------
    text going to stdout
    ----------------------- Captured stderr call ----------------------
    text going to stderr
    ==================== 2 failed in 0.02 seconds =====================

These options can also be customized through a configuration file::

    [pytest]
    log_format = %(asctime)s %(levelname)s %(message)s
    log_date_format = %Y-%m-%d %H:%M:%S

Although the same effect could be achieved through the ``addopts`` setting,
using dedicated options should be preferred since the latter doesn't
force other developers to have ``pytest-catchlog`` installed (while at
the same time, ``addopts`` approach would fail with 'unrecognized arguments'
error). Command line arguments take precedence.

Further it is possible to disable reporting logs on failed tests
completely with::

    py.test --no-print-logs test_pytest_catchlog.py

Shows failed tests in the normal manner as no logs were captured::

    ----------------------- Captured stdout call ----------------------
    text going to stdout
    ----------------------- Captured stderr call ----------------------
    text going to stderr
    ==================== 2 failed in 0.02 seconds =====================

Inside tests it is possible to change the log level for the captured
log messages.  This is supported by the ``caplog`` funcarg::

    def test_foo(caplog):
        caplog.set_level(logging.INFO)
        pass

By default the level is set on the handler used to catch the log
messages, however as a convenience it is also possible to set the log
level of any logger::

    def test_foo(caplog):
        caplog.set_level(logging.CRITICAL, logger='root.baz')
        pass

It is also possible to use a context manager to temporarily change the
log level::

    def test_bar(caplog):
        with caplog.at_level(logging.INFO):
            pass

Again, by default the level of the handler is affected but the level
of any logger can be changed instead with::

    def test_bar(caplog):
        with caplog.at_level(logging.CRITICAL, logger='root.baz'):
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

You can also resort to ``record_tuples`` if all you want to do is to ensure,
that certain messages have been logged under a given logger name with a
given severity and message::

    def test_foo(caplog):
        logging.getLogger().info('boo %s', 'arg')

        assert caplog.record_tuples() == [
            ('root', logging.INFO, 'boo arg'),
        ]

