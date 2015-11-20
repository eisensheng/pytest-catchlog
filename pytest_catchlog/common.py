# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import logging
from contextlib import closing, contextmanager

import py


def get_logger_obj(logger=None):
    """Get a logger object that can be specified by its name, or passed as is.

    Defaults to the root logger.
    """
    if logger is None or isinstance(logger, py.builtin._basestring):
        logger = logging.getLogger(logger)
    return logger


@contextmanager
def logging_at_level(level, logger=None):
    """Context manager that sets the level for capturing of logs."""
    logger = get_logger_obj(logger)

    orig_level = logger.level
    logger.setLevel(level)
    try:
        yield
    finally:
        logger.setLevel(orig_level)


@contextmanager
def logging_using_handler(handler, logger=None):
    """Context manager that safely register a given handler."""
    logger = get_logger_obj(logger)

    if handler in logger.handlers:  # reentrancy
        # Adding the same handler twice would confuse logging system.
        # Just don't do that.
        yield
    else:
        logger.addHandler(handler)
        try:
            yield
        finally:
            logger.removeHandler(handler)


@contextmanager
def catching_logs(handler, filter=None, formatter=None,
                  level=logging.NOTSET, logger=None):
    """Context manager that prepares the whole logging machinery properly."""
    logger = get_logger_obj(logger)

    if filter is not None:
        handler.addFilter(filter)
    if formatter is not None:
        handler.setFormatter(formatter)
    handler.setLevel(level)

    with closing(handler):
        with logging_using_handler(handler, logger):
            with logging_at_level(min(handler.level, logger.level), logger):

                yield handler
