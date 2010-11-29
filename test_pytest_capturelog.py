import py

pytest_plugins = 'pytester', 'capturelog'

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
    assert result.stdout.fnmatch_lines([
            '*- Captured stdout -*',
            'text going to stdout',
            '*- Captured stderr -*',
            'text going to stderr'
            ])
    matching_lines = [line for line in result.outlines if '- Captured log -' in line]
    assert not matching_lines

def test_messages_logged(testdir):
    testdir.makepyfile('''
        import sys
        import logging

        pytest_plugins = 'capturelog'

        def test_foo():
            sys.stdout.write('text going to stdout')
            sys.stderr.write('text going to stderr')
            logging.getLogger().info('text going to logger')
            assert False
        ''')
    result = testdir.runpytest()
    assert result.ret == 1
    fnmatch = result.stdout.fnmatch_lines
    assert fnmatch(['*- Captured log -*', '*text going to logger*'])
    assert fnmatch(['*- Captured stdout -*', 'text going to stdout'])
    assert fnmatch(['*- Captured stderr -*', 'text going to stderr'])

def test_change_level(testdir):
    testdir.makepyfile('''
        import sys
        import logging

        pytest_plugins = 'capturelog'

        def test_foo(capturelog):
            capturelog.setLevel(logging.INFO)
            log = logging.getLogger()
            log.debug('DEBUG level')
            log.info('INFO level')
            assert False
        ''')
    result = testdir.runpytest()
    assert result.ret == 1
    fnmatch = result.stdout.fnmatch_lines
    assert fnmatch(['*- Captured log -*', '*INFO level*'])
    py.test.raises(AssertionError,
                   fnmatch, ['*- Captured log -*', '*DEBUG level*'])

@py.test.mark.skipif('sys.version_info < (2,5)')
def test_with_statement(testdir):
    testdir.makepyfile('''
        from __future__ import with_statement
        import sys
        import logging

        pytest_plugins = 'capturelog'

        def test_foo(capturelog):
            log = logging.getLogger()
            with capturelog(logging.INFO):
                log.debug('DEBUG level')
                log.info('INFO level')
            assert False
        ''')
    result = testdir.runpytest()
    assert result.ret == 1
    fnmatch = result.stdout.fnmatch_lines
    assert fnmatch(['*- Captured log -*', '*INFO level*'])
    py.test.raises(AssertionError,
                   fnmatch, ['*- Captured log -*', '*DEBUG level*'])

def test_raw_record(testdir):
    testdir.makepyfile('''
        import sys
        import logging

        pytest_plugins = 'capturelog'

        def test_foo(capturelog):
            logging.getLogger().info('boo %s', 'arg')
            assert capturelog.raw_records[0].levelname == 'INFO'
            assert capturelog.raw_records[0].msg == 'boo %s'
        ''')
    result = testdir.runpytest()
    assert result.ret == 0
