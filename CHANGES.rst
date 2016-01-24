Changelog
=========

List of notable changes between pytest-catchlog releases.

.. %UNRELEASED_SECTION%

`1.2.2`_
-------------

Released on 2016-01-24 UTC.

- [Bugfix] `#30`_ `#31`_ - Fix ``unicode`` vs ``str`` compatibility issues between Python2 and Python3.
  (Thanks goes to `@sirex`_ for reporting the issue and providing a fix!)

.. _#30: https://github.com/eisensheng/pytest-catchlog/issues/30
.. _#31: https://github.com/eisensheng/pytest-catchlog/issues/31
.. _@sirex: https://github.com/sirex


`1.2.1`_
-------------

Released on 2015-12-07.

- [Bugfix] #18 - Allow ``caplog.records()`` to be modified.  Thanks to Eldar Abusalimov for the PR and Marco Nenciarini for reporting the issue.
- [Bugfix] #15 #17 - Restore Python 2.6 compatibility. (Thanks to Marco Nenciarini!)

.. attention::
    Deprecation warning: the following objects (i.e. functions, properties)
    are slated for removal in the next major release.

    - ``caplog.at_level`` and ``caplog.set_level`` should be used instead of
      ``caplog.atLevel`` and ``caplog.setLevel``.

      The methods ``caplog.atLevel`` and ``caplog.setLevel`` are still
      available but deprecated and not supported since they don't follow
      the PEP8 convention for method names.

    - ``caplog.text``, ``caplog.records`` and
      ``caplog.record_tuples`` were turned into properties.
      They still can be used as regular methods for backward compatibility,
      but that syntax is considered deprecated and scheduled for removal in
      the next major release.


Version 1.2
-----------

Released on 2015-11-08.

- [Feature] #6 - Configure logging message and date format through ini file.
- [Feature] #7 - Also catch logs from setup and teardown stages.
- [Feature] #7 - Replace deprecated ``__multicall__`` use to support future Py.test releases.
- [Feature] #11 - reintroduce ``setLevel`` and ``atLevel`` to retain backward compatibility with pytest-capturelog.  Also the members ``text``, ``records`` and ``record_tuples`` of the ``caplog`` fixture can be used as properties now.

Special thanks for this release goes to Eldar Abusalimov.  He provided all of the changed features.


Version 1.1
-----------

Released on 2015-06-07.

- #2 - Explicitly state Python3 support and add configuration for running
  tests with tox on multiple Python versions. (Thanks to Jeremy Bowman!)
- Add an option to silence logs completely on the terminal.


Version 1.0
-----------

Released on 2014-12-08.

- Add ``record_tuples`` for comparing recorded log entries against expected
  log entries with their logger name, severity and formatted message.
