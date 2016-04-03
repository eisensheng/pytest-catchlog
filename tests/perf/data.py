from __future__ import absolute_import, division, print_function

import io
import json
import os.path
from functools import wraps
from glob import glob
from itertools import chain


def gen_dict(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        return dict(func(*args, **kwargs))
    return decorated


@gen_dict  # {'mode': {'NNNN': benchmark, ...}}
def load_raw_benchmarks(storage, modes):
    for mode in sorted(modes):
        trialmap = {}

        for bench_file in glob(os.path.join(storage, mode,
                                            '[0-9][0-9][0-9][0-9]_*.json')):
            trial_name = os.path.split(bench_file)[1].partition('_')[0]  # NNNN
            with io.open(bench_file, 'rU') as fh:
                data = json.load(fh)
            trialmap[trial_name] = data

        yield mode, trialmap


def all_trial_names(raw_benchmarks):
    return sorted(set(chain.from_iterable(raw_benchmarks.values())))


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
    raw_benchmarks = load_raw_benchmarks(bench_storage, modes)
    trial_names = all_trial_names(raw_benchmarks)
    benchmarks = prepare_benchmarks(raw_benchmarks, trial_names)

    return trial_names, benchmarks
