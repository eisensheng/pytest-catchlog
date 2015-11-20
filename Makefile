.PHONY: docs
.SILENT: init-devel test test-tox test-coverage

all: clean test

clean-coverage:
	-rm .coverage*
	-rm coverage.xml
	-rm -rfv htmlcov

clean-pyc:
	-find . -path './.tox' -prune -or \
		-name '__pycache__' -exec rm -rv {} +
	-find . -path './.tox' -prune -or \
		\( -name '*.pyc' -or -name '*.pyo' \) -exec rm -rv {} +

clean: clean-pyc clean-coverage
	-rm -rv build dist *.egg-info

test:
	py.test -v tests

test-coverage:
	coverage erase
	coverage run --source=pytest_catchlog --branch -m pytest -v
	coverage report
	coverage xml

audit:
	flake8 pytest_catchlog.py

wheel:
	python setup.py bdist_wheel

sdist:
	python setup.py sdist
