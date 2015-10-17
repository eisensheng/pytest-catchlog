Changelog
=========

List of notable changes between pytest-catchlog releases.


Version 1.2
-----------

Yet to be released.

- [Feature] #6 - Configure logging message and date format through ini file. (Thanks to Eldar Abusalimov!)
- [Feature] #7 - Also catch logs from setup and teardown stages. (Thanks to Eldar Abusalimov!)
- [Feature] #7 - Replace deprecated ``__multicall__`` use to support future Py.test releases. (Thanks to Eldar Abusalimov!)


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
