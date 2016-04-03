from __future__ import absolute_import, division, print_function

import logging

import pytest


logger = logging.getLogger('pytest_catchlog.test.perf')


@pytest.fixture(autouse=True)
def bench_runtest(request, benchmark):
    # Using benchmark.weave to patch a runtest hook doesn't seem to work with
    # pytest 2.8.3; for some reason hook gets called more than once, before
    # running benchmark cleanup finalizer, resulting in the
    # "FixtureAlreadyUsed: Fixture can only be used once" error.
    #
    # Use plain old monkey patching instead.
    ihook = request.node.ihook
    saved_hook = ihook.pytest_runtest_call

    def patched_hook(*args, **kwargs):
        ihook.pytest_runtest_call = saved_hook  # restore early
        return benchmark(saved_hook, *args, **kwargs)

    ihook.pytest_runtest_call = patched_hook
    benchmark.group = 'runtest'


@pytest.yield_fixture  # because 'caplog' is also a yield_fixture
def stub():
    """No-op stub used in place of 'caplog'.

    Helps to measure the inevitable overhead of the pytest fixture injector to
    let us exclude it later on.
    """
    yield


def test_fixture_stub(stub):
    logger.info('Testing %r hook performance: %s',
                'catchlog', 'pure runtest hookwrapper overhead')


def test_caplog_fixture(caplog):
    logger.info('Testing %r hook performance: %s',
                'catchlog', 'hookwrapper + caplog fixture overhead')
