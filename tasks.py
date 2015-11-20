# -*- coding: utf-8 -*-
import os
import re
import io
from contextlib import contextmanager
from datetime import datetime

from invoke import task, run

VERSION_FILE = 'pytest_catchlog/__init__.py'
CHANGE_LOG_FILE = 'CHANGES.rst'


def _path_abs_join(*nodes):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), *nodes))


def _path_open(*nodes, **kwargs):
    return io.open(_path_abs_join(*nodes), **kwargs)


def _shell_quote(s):
    """Quote given string to be suitable as input for bash as argument."""
    if not s:
        return "''"
    if re.search(r'[^\w@%+=:,./-]', s) is None:
        return s
    return "'" + s.replace("'", "'\"'\"'") + "'"


def _git_do(*commands, **kwargs):
    """Execute arbitrary git commands."""
    kwargs.setdefault('hide', 'out')
    results = [run('git ' + command, **kwargs).stdout.strip('\n')
               for command in commands]
    return results if len(commands) > 1 else results[0]


def _git_checkout(branch_name):
    """Switches to the given branch name."""
    return _git_do('checkout ' + _shell_quote(branch_name))


@contextmanager
def _git_work_on(branch_name):
    """Work on given branch. Preserves current git branch."""
    original_branch = _git_do('rev-parse --abbrev-ref HEAD')
    try:
        if original_branch != branch_name:
            _git_checkout(branch_name)
        yield
    finally:
        if original_branch and original_branch != branch_name:
            _git_checkout(original_branch)


def _version_find_existing():
    """Returns set of existing versions in this repository.

    This information is backed by previously used version tags
    stored in the git repository.
    """
    git_tags = [y.strip() for y in _git_do('tag -l').split('\n')]

    _version_re = re.compile(r'^v?(\d+)(?:\.(\d+)(?:\.(\d+))?)?$')
    return {tuple(int(n) if n else 0 for n in m.groups())
            for m in (_version_re.match(t) for t in git_tags if t) if m}


def _version_find_latest():
    """Returns the most recent used version number.

    This information is backed by previously used version tags
    stored in the git repository.
    """
    return max(_version_find_existing())


def _version_guess_next(position='minor'):
    """Guess next version.

    A guess for the next version is determined by incrementing given
    position or minor level position in latest existing version.
    """
    try:
        latest_version = list(_version_find_latest())
    except ValueError:
        latest_version = [0, 0, 0]

    position_index = {'major': 0, 'minor': 1, 'patch': 2}[position]
    latest_version[position_index] += 1
    latest_version[position_index + 1:] = [0] * (2 - position_index)
    return tuple(latest_version)


def _version_format(version):
    """Return version in dotted string format."""
    return '.'.join(str(x) for x in version)


def _patch_file(file_path, line_callback):
    """Patch given file with result from line callback.

    Each line will be passed to the line callback.
    The return value of the given callback will determine
    the new content for the file.

    :param str file_path:
        The file to patch.
    :param callable line_callback:
        The patch function to run over each line.
    :return:
        Whenever the file has changed or not.
    :rtype:
        bool
    """
    new_file_content, file_changed = [], False
    with _path_open(file_path) as in_stream:
        for l in (x.strip('\n') for x in in_stream):
            alt_lines = line_callback(l) or [l]
            if alt_lines != [l]:
                file_changed = True
            new_file_content += (x + u'\n' for x in alt_lines)

    new_file_name = file_path + '.new'
    with _path_open(new_file_name, mode='w') as out_stream:
        out_stream.writelines(new_file_content)
        out_stream.flush()
        os.fsync(out_stream.fileno())
    os.rename(new_file_name, file_path)

    return file_changed


def _patch_version(new_version):
    """Patch given version into version file."""
    _patch_version_re = re.compile(r"""^(\s*__version__\s*=\s*(?:"|'))"""
                                   r"""(?:[^'"]*)(?:("|')\s*)$""")

    def __line_callback(line):
        match = _patch_version_re.match(line)
        if match:
            line_head, line_tail = match.groups()
            return [line_head + new_version + line_tail]
    return _patch_file(VERSION_FILE, __line_callback)


def _patch_change_log(new_version):
    """Patch given version into change log file."""
    def __line_callback(line):
        if line == u'`Unreleased`_':
            return [u'`{}`_'.format(new_version)]
        elif line == u'Yet to be released.':
            return [datetime.utcnow().strftime(u'Released on %Y-%m-%d UTC.')]
    return _patch_file(CHANGE_LOG_FILE, __line_callback)


@task(name='changelog-add-stub')
def changelog_add_stub():
    """Add new version changes stub to changelog file."""
    def __line_callback(line):
        if line == u'.. %UNRELEASED_SECTION%':
            return [u'.. %UNRELEASED_SECTION%',
                    u'',
                    u'`Unreleased`_',
                    u'-------------',
                    u'',
                    u'Yet to be released.',
                    u'']
    return _patch_file(CHANGE_LOG_FILE, __line_callback)


@task()
def mkrelease(position='minor'):
    """Merge development state into Master Branch and tags a new Release."""
    next_version = _version_format(_version_guess_next(position))
    with _git_work_on('develop'):
        patched_files = []
        if _patch_version(next_version):
            patched_files.append(VERSION_FILE)

        if _patch_change_log(next_version):
            patched_files.append(CHANGE_LOG_FILE)

        if patched_files:
            patched_files = ' '.join(_shell_quote(x) for x in patched_files)
            _git_do('diff --color=always -- ' + patched_files,
                    ("commit -m 'Bump Version to {0}' -- {1}"
                     .format(next_version, patched_files)),
                    hide=None)

        with _git_work_on('master'):
            message = _shell_quote('Release {0}'.format(next_version))
            _git_do('merge --no-ff --no-edit -m {0} develop'.format(message),
                    "tag -a -m {0} {1}".format(message, next_version))
