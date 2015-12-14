from __future__ import absolute_import, division, print_function

import os.path

import py
import pytest


BENCH_DIR = py.path.local(__file__).dirpath('bench')


mode_args_map = {
    'default':   [],
    'noplugin':  ['-pno:pytest_catchlog'],
    'noprint':   ['--no-print-logs'],
    'nocapture': ['-s'],
}


def path_in_dir(path, dir=py.path.local(__file__).dirpath()):
    return (dir.common(path) == dir)


def pytest_ignore_collect(path):
    if path_in_dir(path, BENCH_DIR):
        # Tests from that directory never run through test discovery.
        #
        # Instead, they run either with the BENCH_DIR specified explicitly
        # both as a target and a 'confcutdir' or when the BENCH_DIR itself
        # is a 'rootdir' (CWD). In any case this conftest is not processed
        # at all, and this hook doesn't run when running tests from the
        # BENCH_DIR.
        return True


def pytest_itemcollected(item):
    """This is only called for local tests (under tests/perf_runner/)."""
    if path_in_dir(item.fspath):
        item.add_marker('_perf_test')


def pytest_collection_modifyitems(session, config, items):
    """This is called after collection (of all tests) has been performed."""
    run_perf = config.getoption('run_perf')
    if run_perf in ('yes', 'check'):
        return
    perf_only = (run_perf == 'only')

    items[:] = [item
                for item in items
                if bool(item.get_marker('_perf_test')) == perf_only]


def pytest_terminal_summary(terminalreporter):
    """Add additional section in terminal summary reporting."""
    config = terminalreporter.config

    if config.getoption('run_perf') in ('yes', 'only'):
        passed = terminalreporter.stats.get('passed', [])
        for rep in passed:
            if '_perf_test' not in rep.keywords:
                continue

            out = '\n'.join(s for _, s in rep.get_sections('Captured stdout'))
            if out:
                fspath, lineno, name = rep.location
                terminalreporter.write_sep("-", 'Report from {0}'.format(name))
                terminalreporter.write(out)


@pytest.fixture(params=sorted(mode_args_map))
def mode(request):
    return request.param


@pytest.fixture
def mode_args(mode):
    return mode_args_map[mode]


@pytest.fixture
def storage_dir(pytestconfig, mode):
    storage = pytestconfig.getoption('--benchmark-storage')
    return os.path.join(storage, mode)


@pytest.fixture
def bench_dir():
    return BENCH_DIR
