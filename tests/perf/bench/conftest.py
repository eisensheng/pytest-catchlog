from __future__ import absolute_import, division, print_function

import pytest


class CatchLogStub(object):
    """Provides a no-op 'caplog' fixture fallback."""

    @pytest.yield_fixture
    def caplog(self):
        yield


@pytest.mark.trylast
def pytest_configure(config):
    if not pytest.config.pluginmanager.hasplugin('pytest_catchlog'):
        config.pluginmanager.register(CatchLogStub(), 'caplog_stub')
