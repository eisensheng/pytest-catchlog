import py

pytest_plugins = 'pytester', 'catchlog'


def test_nothing_logged(testdir):
    testdir.makepyfile('''
        import sys
        import logging

        pytest_plugins = 'catchlog'

        def test_foo():
            sys.stdout.write('text going to stdout')
            sys.stderr.write('text going to stderr')
            assert False
        ''')
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(['*- Captured stdout -*',
                                 'text going to stdout'])
    result.stdout.fnmatch_lines(['*- Captured stderr -*',
                                 'text going to stderr'])
    py.test.raises(Exception, result.stdout.fnmatch_lines,
                   ['*- Captured log -*'])


def test_messages_logged(testdir):
    testdir.makepyfile('''
        import sys
        import logging

        pytest_plugins = 'catchlog'

        def test_foo():
            sys.stdout.write('text going to stdout')
            sys.stderr.write('text going to stderr')
            logging.getLogger().info('text going to logger')
            assert False
        ''')
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(['*- Captured log -*',
                                 '*text going to logger*'])
    result.stdout.fnmatch_lines(['*- Captured stdout -*',
                                 'text going to stdout'])
    result.stdout.fnmatch_lines(['*- Captured stderr -*',
                                 'text going to stderr'])


def test_change_level(testdir):
    testdir.makepyfile('''
        import sys
        import logging

        pytest_plugins = 'catchlog'

        def test_foo(caplog):
            caplog.setLevel(logging.INFO)
            log = logging.getLogger()
            log.debug('handler DEBUG level')
            log.info('handler INFO level')

            caplog.setLevel(logging.CRITICAL, logger='root.baz')
            log = logging.getLogger('root.baz')
            log.warning('logger WARNING level')
            log.critical('logger CRITICAL level')

            assert False
        ''')
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(['*- Captured log -*',
                                 '*handler INFO level*',
                                 '*logger CRITICAL level*'])
    py.test.raises(Exception, result.stdout.fnmatch_lines,
                   ['*- Captured log -*', '*handler DEBUG level*'])
    py.test.raises(Exception, result.stdout.fnmatch_lines,
                   ['*- Captured log -*', '*logger WARNING level*'])


@py.test.mark.skipif('sys.version_info < (2,5)')
def test_with_statement(testdir):
    testdir.makepyfile('''
        from __future__ import with_statement
        import sys
        import logging

        pytest_plugins = 'catchlog'

        def test_foo(caplog):
            with caplog.atLevel(logging.INFO):
                log = logging.getLogger()
                log.debug('handler DEBUG level')
                log.info('handler INFO level')

                with caplog.atLevel(logging.CRITICAL, logger='root.baz'):
                    log = logging.getLogger('root.baz')
                    log.warning('logger WARNING level')
                    log.critical('logger CRITICAL level')

            assert False
        ''')
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(['*- Captured log -*',
                                 '*handler INFO level*',
                                 '*logger CRITICAL level*'])
    py.test.raises(Exception, result.stdout.fnmatch_lines,
                   ['*- Captured log -*', '*handler DEBUG level*'])
    py.test.raises(Exception, result.stdout.fnmatch_lines,
                   ['*- Captured log -*', '*logger WARNING level*'])


def test_log_access(testdir):
    testdir.makepyfile('''
        import sys
        import logging

        pytest_plugins = 'catchlog'

        def test_foo(caplog):
            logging.getLogger().info('boo %s', 'arg')
            assert caplog.records()[0].levelname == 'INFO'
            assert caplog.records()[0].msg == 'boo %s'
            assert 'boo arg' in caplog.text()
        ''')
    result = testdir.runpytest()
    assert result.ret == 0


def test_funcarg_help(testdir):
    result = testdir.runpytest('--funcargs')
    result.stdout.fnmatch_lines(['*caplog*'])
