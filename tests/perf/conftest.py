from __future__ import absolute_import, division, print_function

import os.path
try:
    from builtins import __dict__ as builtins
except ImportError:  # Python 2
    from __builtin__ import __dict__ as builtins

import py
import pytest

from .data import gen_dict, load_benchmarks
from .plot import make_plot


BENCH_DIR = py.path.local(__file__).dirpath('bench')


mode_args_map = {
    'default':   [],
    'noprint':   ['--no-print-logs'],
    'nocapture': ['-s'],
    'off':       ['-p', 'no:pytest_catchlog'],
}


def pytest_configure(config):
    if (config.getoption('run_perf') in ('yes', 'only') and
        config.getoption('perf_graph_name')):

        expr = config.getoption('perf_expr_primary')
        expr2 = config.getoption('perf_expr_secondary')
        if not (expr or expr2):
            raise pytest.UsageError('perf-graph: Nothing to plot, '
                                    'see --perf-expr')


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

    handle_perf_graph(config, terminalreporter)


def handle_perf_graph(config, terminalreporter):
    output_file = config.getoption('perf_graph_name')
    if not output_file:
        return

    bench_storage = config.getoption('--benchmark-storage')
    output_file = os.path.join(bench_storage, output_file)

    trial_names, benchmarks = load_benchmarks(bench_storage,
                                              modes=sorted(mode_args_map))
    if not trial_names:
        terminalreporter.write_line(
            'perf-graph: No benchmarks found in {0}'.format(bench_storage),
            yellow=True, bold=True)
        return

    expr = config.getoption('perf_expr_primary')
    expr2 = config.getoption('perf_expr_secondary')

    history = eval_benchmark_expr(expr, benchmarks)
    history2 = eval_benchmark_expr(expr2, benchmarks)

    plot = make_plot(
        trial_names=trial_names,
        history=history,
        history2=history2,
        expr=expr,
        expr2=expr2,
    )
    plot.render_to_file(output_file)

    terminalreporter.write_line(
        'perf-graph: Saved graph into {0}'.format(output_file),
        green=True, bold=True)


@gen_dict
def eval_benchmark_expr(expr, benchenvs, **kwargs):
    for mode, envlist in benchenvs.items():
        yield mode, [BenchmarkEnv(benchenv, **kwargs).evaluate(expr)
                     for benchenv in envlist]


class BenchmarkEnv(dict):
    """Holds results of benchmark tests.

    Allows unambiguous access through a key substring: e.g. just 'foo' for
    'test_foo_stuff' (but at the same time there must not be 'test_some_food').
    """
    __slots__ = ()

    class UndefinedValue(ValueError):
        pass

    def __missing__(self, lookup):
        if lookup in builtins:
            raise KeyError  # to make builtins handled as usual

        found = None
        for key in self:
            if lookup in key:  # substring match
                if found is not None:
                    raise pytest.UsageError('Ambiguous benchmark ID: '
                                            'multiple tests match {lookup!r} '
                                            '(at least {found!r} and {key!r})'
                                            .format(**locals()))
                found = key
        if found is None:
            raise pytest.UsageError('Unknown benchmark ID: '
                                    'no test matches {lookup!r}: {self}'
                                    .format(**locals()))
        ret = self[found]
        if ret is None:
            # If an expression involves None (i.e. undefined),
            # the result must be also None.
            raise self.UndefinedValue('Missing proper benchmark value')

        return ret

    def evaluate(self, expr):
        """Evaluate an expression using this environment as globals."""
        try:
            return eval(expr.strip() or 'None', {}, self)
        except self.UndefinedValue:
            return None


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
