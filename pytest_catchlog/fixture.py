# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import functools
import logging

import pytest
import py

from pytest_catchlog.common import catching_logs, logging_at_level


class LogCaptureFixture(object):
    """Provides access and control of log capturing."""

    @property
    def handler(self):
        return self._item.catch_log_handler

    def __init__(self, item):
        """Creates a new funcarg."""
        self._item = item

    @property
    def text(self):
        """Returns the log text."""
        return self.handler.stream.getvalue()

    @property
    def records(self):
        """Returns the list of log records."""
        return self.handler.records

    @property
    def record_tuples(self):
        """Returns a list of a striped down version of log records intended
        for use in assertion comparison.

        The format of the tuple is:

            (logger_name, log_level, message)
        """
        return [(r.name, r.levelno, r.getMessage()) for r in self.records]

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
        return logging_at_level(level, obj)


class CallablePropertyMixin(object):
    """Backward compatibility for functions that became properties."""

    @classmethod
    def compat_property(cls, func):
        if isinstance(func, property):
            make_property = func.getter
            func = func.fget
        else:
            make_property = property

        @functools.wraps(func)
        def getter(self):
            naked_value = func(self)
            ret = cls(naked_value)
            ret._naked_value = naked_value
            ret._warn_compat = self._warn_compat
            ret._prop_name = func.__name__
            return ret

        return make_property(getter)

    def __call__(self):
        self._warn_compat(old="'caplog.{0}()' syntax".format(self._prop_name),
                          new="'caplog.{0}' property".format(self._prop_name))
        return self._naked_value  # to let legacy clients modify the object


class CallableList(CallablePropertyMixin, list):
    pass


class CallableStr(CallablePropertyMixin, py.builtin.text):
    pass


class CompatLogCaptureFixture(LogCaptureFixture):
    """Backward compatibility with pytest-capturelog."""

    def _warn_compat(self, old, new):
        self._item.warn(code='L1',
                        message=("{0} is deprecated, use {1} instead"
                                 .format(old, new)))

    @CallableStr.compat_property
    def text(self):
        return super(CompatLogCaptureFixture, self).text

    @CallableList.compat_property
    def records(self):
        return super(CompatLogCaptureFixture, self).records

    @CallableList.compat_property
    def record_tuples(self):
        return super(CompatLogCaptureFixture, self).record_tuples

    def setLevel(self, level, logger=None):
        self._warn_compat(old="'caplog.setLevel()'",
                          new="'caplog.set_level()'")
        return self.set_level(level, logger)

    def atLevel(self, level, logger=None):
        self._warn_compat(old="'caplog.atLevel()'",
                          new="'caplog.at_level()'")
        return self.at_level(level, logger)


@pytest.fixture
def caplog(request):
    """Access and control log capturing.

    Captured logs are available through the following methods::

    * caplog.text()          -> string containing formatted log output
    * caplog.records()       -> list of logging.LogRecord instances
    * caplog.record_tuples() -> list of (logger_name, level, message) tuples
    """
    return CompatLogCaptureFixture(request.node)

capturelog = caplog
