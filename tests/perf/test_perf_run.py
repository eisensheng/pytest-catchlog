from __future__ import absolute_import, division, print_function

import os
import os.path
import sys
import subprocess

import pytest


PYTEST_PATH = (os.path.abspath(pytest.__file__.rstrip("oc"))
               .replace("$py.class", ".py"))

POPEN_CLEANUP_TIMEOUT = 3 if (sys.version_info[0] >= 3) else 0  # Py3k only


@pytest.fixture
def popen(request):
    env = os.environ.copy()
    cwd = os.getcwd()
    pythonpath = [cwd]
    if env.get('PYTHONPATH'):
        pythonpath.append(env['PYTHONPATH'])
    env['PYTHONPATH'] = os.pathsep.join(pythonpath)

    def popen_wait(*args, **kwargs):
        __tracebackhide__ = True

        args = [str(arg) for arg in args]
        kwargs['env'] = dict(env, **kwargs.get('env', {}))

        print('Running', ' '.join(args))
        popen = subprocess.Popen(args, **kwargs)
        try:
            ret = popen.wait()
        except KeyboardInterrupt as e:
            # Before proceeding to the exit, give the child the last chance to
            # cleanup. Otherwise, benchmark storage may happen to be read
            # during preparing the final reporting (see ls_bench_storage(),
            # called from handle_perf_graph()), while being concurrently
            # modified by the child (pytest-benchmark writing results files).
            try:
                if POPEN_CLEANUP_TIMEOUT:
                    popen.wait(timeout=POPEN_CLEANUP_TIMEOUT)
            finally:
                raise e
        else:
            assert ret == 0

    return popen_wait


@pytest.fixture
def color(pytestconfig):
    reporter = pytestconfig.pluginmanager.getplugin('terminalreporter')
    try:
        return 'yes' if reporter.writer.hasmarkup else 'no'
    except AttributeError:
        return pytestconfig.option.color


@pytest.fixture
def verbosity(pytestconfig):
    v = pytestconfig.option.verbose or -1
    return ('v' if v > 0 else 'q') * abs(v)

@pytest.fixture
def base_args(bench_dir, verbosity, color):
    return [
        bench_dir,
        '--confcutdir={0}'.format(bench_dir),
        '-x',
        '-{0}'.format(verbosity),
        '-rw',
        '--color={0}'.format(color),
    ]


@pytest.fixture
def bench_args(pytestconfig, storage_dir):
    if pytestconfig.getoption('run_perf') != 'check':
        return [
            '--benchmark-only',
            '--benchmark-disable-gc',
            '--benchmark-autosave',
            '--benchmark-storage={0}'.format(storage_dir),
        ]
    else:
        return ['--benchmark-disable']


@pytest.fixture
def perf_args(base_args, mode_args, bench_args):
    return base_args + mode_args + bench_args


def test_perf_run(popen, perf_args):
    popen(sys.executable, PYTEST_PATH, *perf_args)
