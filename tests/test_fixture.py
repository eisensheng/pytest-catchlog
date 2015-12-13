# -*- coding: utf-8 -*-
import sys
import logging

import pytest

logger = logging.getLogger(__name__)
sublogger = logging.getLogger(__name__+'.baz')

u = (lambda x: x.decode('utf-8')) if sys.version_info < (3,) else (lambda x: x)


def test_fixture_help(testdir):
    result = testdir.runpytest('--fixtures')
    result.stdout.fnmatch_lines(['*caplog*'])


def test_change_level(caplog):
    caplog.set_level(logging.INFO)
    logger.debug('handler DEBUG level')
    logger.info('handler INFO level')

    caplog.set_level(logging.CRITICAL, logger=sublogger.name)
    sublogger.warning('logger WARNING level')
    sublogger.critical('logger CRITICAL level')

    assert 'DEBUG' not in caplog.text
    assert 'INFO' in caplog.text
    assert 'WARNING' not in caplog.text
    assert 'CRITICAL' in caplog.text


def test_with_statement(caplog):
    with caplog.at_level(logging.INFO):
        logger.debug('handler DEBUG level')
        logger.info('handler INFO level')

        with caplog.at_level(logging.CRITICAL, logger=sublogger.name):
            sublogger.warning('logger WARNING level')
            sublogger.critical('logger CRITICAL level')

    assert 'DEBUG' not in caplog.text
    assert 'INFO' in caplog.text
    assert 'WARNING' not in caplog.text
    assert 'CRITICAL' in caplog.text


def test_log_access(caplog):
    logger.info('boo %s', 'arg')
    assert caplog.records[0].levelname == 'INFO'
    assert caplog.records[0].msg == 'boo %s'
    assert 'boo arg' in caplog.text


def test_record_tuples(caplog):
    logger.info('boo %s', 'arg')

    assert caplog.record_tuples == [
        (__name__, logging.INFO, 'boo arg'),
    ]


def test_unicode(caplog):
    logger.info(u('bū'))
    assert caplog.records[0].levelname == 'INFO'
    assert caplog.records[0].msg == u('bū')
    assert u('bū') in caplog.text
