Changelog
=========

List of notable changes between pytest-catchlog releases.

.. %UNRELEASED_SECTION%

`Unreleased`_
-------------

Yet to be released.


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
