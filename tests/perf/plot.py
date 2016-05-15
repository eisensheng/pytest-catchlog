from __future__ import absolute_import, division, print_function

import math

import pygal
from pygal.style import DefaultStyle

try:
    import pygaljs
except ImportError:
    opts = {}
else:
    opts = {"js": [pygaljs.uri("2.0.x", "pygal-tooltips.js")]}

opts["css"] = [
    "file://style.css",
    "file://graph.css",
    """inline:
        .axis.x text {
            text-anchor: middle !important;
        }
        .tooltip .value {
            font-size: 1em !important;
        }
    """
]


def log_ceil(x):
    x = float(x)
    exponent = math.floor(math.log10(x))
    exp_mult = math.pow(10, exponent)
    mantissa = x / exp_mult
    return math.ceil(mantissa) * exp_mult


def history_range(history):
    max_ = max(v for serie in history.values() for v in serie)
    if max_ > 0:
        return (0, log_ceil(max_))


def make_plot(trial_names, history, history2, expr, expr2):
    style = DefaultStyle(colors=[
            '#ED6C1D',  # 3
            '#EDC51E',  # 4
            '#BCED1E',  # 5
            '#63ED1F',  # 6
            '#1FED34',  # 7
            '#ED1D27',  # 2
        ][:len(history)] + [
            '#A71DED',  # -3
            '#4F1EED',  # -4
            '#1E45ED',  # -5
            '#1F9EED',  # -6
            '#1FEDE4',  # -7
            '#ED1DDA',  # -2
        ][:len(history2)]
    )

    plot = pygal.Line(
        title="Speed in seconds",
        x_title="Trial",
        x_labels=trial_names,
        x_label_rotation=15,
        include_x_axis=True,
        human_readable=True,
        range=history_range(history),
        secondary_range=history_range(history2),
        style=style,
        stroke_style={'width': 2, 'dasharray': '20, 4'},
        **opts
    )

    for mode in sorted(history):
        serie = [{'value': value, 'label': expr}
                 for value in history[mode]]
        plot.add(mode, serie, stroke_style={'dasharray': 'none'})

    for mode in sorted(history2):
        serie = [{'value': value, 'label': expr2}
                 for value in history2[mode]]
        plot.add(mode, serie, secondary=True)

    return plot
