# coding: utf-8

import sys

import pytest

pytest_plugins = 'pytester'


def test_nothing_logged(testdir):
    testdir.makepyfile('''
        import sys

        def test_foo():
            sys.stdout.write('text going to stdout')
            sys.stderr.write('text going to stderr')
            assert False
        ''')
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(['*- Captured stdout call -*',
                                 'text going to stdout'])
    result.stdout.fnmatch_lines(['*- Captured stderr call -*',
                                 'text going to stderr'])
    with pytest.raises(pytest.fail.Exception):
        result.stdout.fnmatch_lines(['*- Captured *log call -*'])


def test_messages_logged(testdir):
    testdir.makepyfile('''
        import sys
        import logging

        logger = logging.getLogger(__name__)

        def test_foo():
            sys.stdout.write('text going to stdout')
            sys.stderr.write('text going to stderr')
            logger.info('text going to logger')
            assert False
        ''')
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(['*- Captured *log call -*',
                                 '*text going to logger*'])
    result.stdout.fnmatch_lines(['*- Captured stdout call -*',
                                 'text going to stdout'])
    result.stdout.fnmatch_lines(['*- Captured stderr call -*',
                                 'text going to stderr'])


def test_setup_logging(testdir):
    testdir.makepyfile('''
        import logging

        logger = logging.getLogger(__name__)

        def setup_function(function):
            logger.info('text going to logger from setup')

        def test_foo():
            logger.info('text going to logger from call')
            assert False
        ''')
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(['*- Captured *log setup -*',
                                 '*text going to logger from setup*',
                                 '*- Captured *log call -*',
                                 '*text going to logger from call*'])


def test_teardown_logging(testdir):
    testdir.makepyfile('''
        import logging

        logger = logging.getLogger(__name__)

        def test_foo():
            logger.info('text going to logger from call')

        def teardown_function(function):
            logger.info('text going to logger from teardown')
            assert False
        ''')
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(['*- Captured *log call -*',
                                 '*text going to logger from call*',
                                 '*- Captured *log teardown -*',
                                 '*text going to logger from teardown*'])


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

            assert False
        ''')
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(['*- Captured *log call -*',
                                 '*handler INFO level*',
                                 '*logger CRITICAL level*'])
    with pytest.raises(pytest.fail.Exception):
        result.stdout.fnmatch_lines(['*- Captured *log call -*',
                                     '*handler DEBUG level*'])
    with pytest.raises(pytest.fail.Exception):
        result.stdout.fnmatch_lines(['*- Captured *log call -*',
                                     '*handler WARNING level*'])


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

            assert False
        ''')
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(['*- Captured *log call -*',
                                 '*handler INFO level*',
                                 '*logger CRITICAL level*'])
    with pytest.raises(pytest.fail.Exception):
        result.stdout.fnmatch_lines(['*- Captured *log call -*',
                                     '*handler DEBUG level*'])
    with pytest.raises(pytest.fail.Exception):
        result.stdout.fnmatch_lines(['*- Captured *log call -*',
                                     '*handler WARNING level*'])


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


def test_funcarg_help(testdir):
    result = testdir.runpytest('--funcargs')
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


def test_disable_log_capturing(testdir):
    testdir.makepyfile('''
        import sys
        import logging

        logger = logging.getLogger(__name__)

        def test_foo(caplog):
            sys.stdout.write('text going to stdout')
            logger.warning('catch me if you can!')
            sys.stderr.write('text going to stderr')
            assert False
        ''')
    result = testdir.runpytest('--no-print-logs')
    print(result.stdout)
    assert result.ret == 1
    result.stdout.fnmatch_lines(['*- Captured stdout call -*',
                                 'text going to stdout'])
    result.stdout.fnmatch_lines(['*- Captured stderr call -*',
                                 'text going to stderr'])
    with pytest.raises(pytest.fail.Exception):
        result.stdout.fnmatch_lines(['*- Captured *log call -*'])


def test_disable_log_capturing_ini(testdir):
    testdir.makeini(
        '''
        [pytest]
        log_print=False
        '''
    )
    testdir.makepyfile('''
        import sys
        import logging

        logger = logging.getLogger(__name__)

        def test_foo(caplog):
            sys.stdout.write('text going to stdout')
            logger.warning('catch me if you can!')
            sys.stderr.write('text going to stderr')
            assert False
        ''')
    result = testdir.runpytest()
    print(result.stdout)
    assert result.ret == 1
    result.stdout.fnmatch_lines(['*- Captured stdout call -*',
                                 'text going to stdout'])
    result.stdout.fnmatch_lines(['*- Captured stderr call -*',
                                 'text going to stderr'])
    with pytest.raises(pytest.fail.Exception):
        result.stdout.fnmatch_lines(['*- Captured *log call -*'])
