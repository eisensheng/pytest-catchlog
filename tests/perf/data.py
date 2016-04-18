from __future__ import absolute_import, division, print_function

import io
import json
import os.path
from collections import defaultdict
from functools import wraps
from glob import glob
from itertools import chain


def gen_dict(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        return dict(func(*args, **kwargs))
    return decorated


def ls_bench_storage(bench_storage, modes):
    # NNNN just reflects the pytest-benchmark result files naming scheme:
    # NNNN_commit*.json, that is, 0001_commit*.json, 0002_commit*.json, ...
    nnnn_files_map = defaultdict(dict)  # {'NNNN': {'mode': 'filename'}}
    garbage_files = set()

    for mode in modes:
        for filename in glob(os.path.join(bench_storage, mode,
                                          '[0-9][0-9][0-9][0-9]_*.json')):
            mode_dirname, basename = os.path.split(filename)
            nnnn = os.path.splitext(basename)[0][:12]  # NNNN_commit
            mode_nnnn_files = glob(os.path.join(mode_dirname, nnnn + '*.json'))
            if len(mode_nnnn_files) != 1:
                garbage_files.update(mode_nnnn_files)
            else:
                nnnn_files_map[nnnn][mode] = filename

    benchmark_files = defaultdict(dict)  # {'mode': {'NNNN': 'filename'}}

    for nnnn, nnnn_files in nnnn_files_map.items():
        if len(nnnn_files) != len(modes):
            # for gf in nnnn_files.values():
            #     print('>>>', gf)
            garbage_files.update(nnnn_files.values())
        else:
            for mode, filename in nnnn_files.items():
                benchmark_files[mode][nnnn] = filename

    return sorted(nnnn_files_map), dict(benchmark_files), sorted(garbage_files)


@gen_dict  # {'mode': {'NNNN': benchmark, ...}}
def load_raw_benchmarks(benchmark_files):
    for mode, filemap in benchmark_files.items():
        trialmap = {}

        for trial_name, filename in filemap.items():
            with io.open(filename, 'rU') as fh:
                trialmap[trial_name] = json.load(fh)

        yield mode, trialmap


@gen_dict  # {'mode': [{'test': min}...]}
def prepare_benchmarks(raw_benchmarks, trial_names):
    for mode, trialmap in raw_benchmarks.items():
        envlist = []

        for trial_name in trial_names:
            trial = trialmap.get(trial_name, {}).get('benchmarks', [])

            benchenv = dict((bench['fullname'], bench['stats'].get('min'))
                            for bench in trial)
            envlist.append(benchenv)

        yield mode, envlist


def load_benchmarks(bench_storage, modes):
    trial_names, benchmark_files, _ = ls_bench_storage(bench_storage, modes)
    return load_benchmarks_from_files(benchmark_files, trial_names)


def load_benchmarks_from_files(benchmark_files, trial_names):
    raw_benchmarks = load_raw_benchmarks(benchmark_files)
    benchmarks = prepare_benchmarks(raw_benchmarks, trial_names)
    return benchmarks
