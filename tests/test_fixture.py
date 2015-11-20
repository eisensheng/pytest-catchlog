# -*- coding: utf-8 -*-
import sys

import pytest


def test_change_level(testdir):
    testdir.makepyfile('''
        import logging

        logger = logging.getLogger(__name__)
        sublogger = logging.getLogger(__name__+'.baz')

        def test_foo(caplog):
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
        ''')
    result = testdir.runpytest()
    assert result.ret == 0


def test_with_statement(testdir):
    testdir.makepyfile('''
        import logging

        logger = logging.getLogger(__name__)
        sublogger = logging.getLogger(__name__+'.baz')

        def test_foo(caplog):
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
        ''')
    result = testdir.runpytest()
    assert result.ret == 0


def test_log_access(testdir):
    testdir.makepyfile('''
        import logging

        logger = logging.getLogger(__name__)

        def test_foo(caplog):
            logger.info('boo %s', 'arg')
            assert caplog.records[0].levelname == 'INFO'
            assert caplog.records[0].msg == 'boo %s'
            assert 'boo arg' in caplog.text
        ''')
    result = testdir.runpytest()
    assert result.ret == 0


def test_fixture_help(testdir):
    result = testdir.runpytest('--fixtures')
    result.stdout.fnmatch_lines(['*caplog*'])


def test_record_tuples(testdir):
    testdir.makepyfile('''
        import logging

        logger = logging.getLogger(__name__)

        def test_foo(caplog):
            logger.info('boo %s', 'arg')

            assert caplog.record_tuples == [
                (__name__, logging.INFO, 'boo arg'),
            ]
        ''')
    result = testdir.runpytest()
    assert result.ret == 0


def test_unicode(testdir):
    u = lambda x: x.decode('utf-8') if sys.version_info < (3,) else x
    testdir.makepyfile(u('''
        # coding: utf-8

        import sys
        import logging

        logger = logging.getLogger(__name__)

        u = lambda x: x.decode('utf-8') if sys.version_info < (3,) else x

        def test_foo(caplog):
            logger.info(u('bū'))
            assert caplog.records[0].levelname == 'INFO'
            assert caplog.records[0].msg == u('bū')
            assert u('bū') in caplog.text
        '''))
    result = testdir.runpytest()
    assert result.ret == 0


def test_compat_camel_case_aliases(testdir):
    testdir.makepyfile('''
        import logging

        logger = logging.getLogger(__name__)

        def test_foo(caplog):
            caplog.setLevel(logging.INFO)
            logger.debug('boo!')

            with caplog.atLevel(logging.WARNING):
                logger.info('catch me if you can')
        ''')
    result = testdir.runpytest()
    assert result.ret == 0

    with pytest.raises(pytest.fail.Exception):
        result.stdout.fnmatch_lines(['*- Captured *log call -*'])

    result = testdir.runpytest('-rw')
    assert result.ret == 0
    result.stdout.fnmatch_lines('''
        =*warning summary*=
        *WL1*test_compat_camel_case_aliases*caplog.setLevel()*deprecated*
        *WL1*test_compat_camel_case_aliases*caplog.atLevel()*deprecated*
    ''')


def test_compat_properties(testdir):
    testdir.makepyfile('''
        import logging

        logger = logging.getLogger(__name__)

        def test_foo(caplog):
            logger.info('boo %s', 'arg')

            assert caplog.text    == caplog.text()    == str(caplog.text)
            assert caplog.records == caplog.records() == list(caplog.records)
            assert (caplog.record_tuples ==
                    caplog.record_tuples() == list(caplog.record_tuples))
        ''')
    result = testdir.runpytest()
    assert result.ret == 0

    result = testdir.runpytest('-rw')
    assert result.ret == 0
    result.stdout.fnmatch_lines('''
        =*warning summary*=
        *WL1*test_compat_properties*caplog.text()*deprecated*
        *WL1*test_compat_properties*caplog.records()*deprecated*
        *WL1*test_compat_properties*caplog.record_tuples()*deprecated*
    ''')


def test_compat_records_modification(testdir):
    testdir.makepyfile('''
        import logging

        logger = logging.getLogger(__name__)

        def test_foo(caplog):
            logger.info('boo %s', 'arg')
            assert caplog.records
            assert caplog.records()

            del caplog.records()[:]  # legacy syntax
            assert not caplog.records
            assert not caplog.records()

            logger.info('foo %s', 'arg')
            assert caplog.records
            assert caplog.records()
        ''')
    result = testdir.runpytest()
    assert result.ret == 0
