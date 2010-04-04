import py

pytest_plugins = "pytester", "capturelog"

def test_no_logging_import(testdir):
    testdir.makepyfile('''
        import sys

        def test_foo():
            assert 'logging' not in sys.modules, 'logging was imported'
        ''')
    result = testdir.runpytest('--nocapturelog')
    assert result.ret == 0
    assert result.stdout.fnmatch_lines([
            '*1 passed*'
            ])

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

        def test_foo():
            sys.stdout.write('text going to stdout')
            sys.stderr.write('text going to stderr')
            logging.getLogger().info('text going to logger')
            assert False
        ''')
    result = testdir.runpytest()
    assert result.ret == 1
    assert result.stdout.fnmatch_lines([
            '*- Captured log -*',
            '*text going to logger*',
            '*- Captured stdout -*',
            'text going to stdout',
            '*- Captured stderr -*',
            'text going to stderr'
            ])
