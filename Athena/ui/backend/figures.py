"""
Latitude MedTech — figure helpers for generated deliverables
============================================================
Render brand-styled charts to PNG under ``documents/figures/`` and return the
file path, ready to embed in a deliverable via Markdown::

    from figures import bar_chart
    p = bar_chart("Time to clearance", ["Projected", "Latitude"], [14, 8],
                  ylabel="Months", highlight=1, note="Illustrative figures.")
    content = f"![Figure 1. Time to 510(k) clearance.]({p})"
    # ...then POST content to /api/documents/generate

The backend runs on voice/venv, which has matplotlib + Pillow. matplotlib is
imported lazily so a missing install never blocks server startup. Extend this
module with new chart/diagram builders as deliverables require them.
"""
from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime

ATHENA      = Path(__file__).resolve().parents[2]
FIGURES_DIR = ATHENA / "documents" / "figures"

# Latitude brand palette — must match generate_docx() in server.py
NAVY  = "#1A1A1A"
SLATE = "#2C3E50"
BLUE  = "#5B7FA6"
MUTED = "#8A8680"
GREY  = "#B8BCC2"
RULE  = "#E3E6EA"


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:50] or "figure"


def _new_axes(figsize):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Calibri", "Arial", "DejaVu Sans"]
    fig, ax = plt.subplots(figsize=figsize)
    return plt, fig, ax


def _save(fig, name: str) -> str:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out = FIGURES_DIR / f"{datetime.now().strftime('%Y%m%d')}_{_slug(name)}.png"
    fig.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
    return str(out)


def bar_chart(title, labels, values, ylabel: str = "", note: str = "",
              highlight=None, figsize=(9, 5)) -> str:
    """Brand-styled vertical bar chart. Returns the saved PNG path.

    title      chart title (also used to name the file)
    labels     x-axis category labels
    values     numeric bar heights
    ylabel     y-axis label (optional)
    note       small caption under the plot, e.g. an "illustrative" disclaimer
    highlight  index of the bar to accent in brand blue (others render grey)
    """
    plt, fig, ax = _new_axes(figsize)
    colors = [BLUE if (highlight is not None and i == highlight) else GREY
              for i in range(len(values))]
    bars = ax.bar([str(l) for l in labels], values, width=0.55, color=colors, zorder=3)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:g}",
                ha="center", va="bottom", fontsize=12, fontweight="bold", color=SLATE)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10.5, color=NAVY)
    ax.set_title(title, fontsize=14, fontweight="bold", color=NAVY, loc="left", pad=14)
    ax.set_ylim(0, (max(values) * 1.18) if values else 1)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(RULE)
    ax.tick_params(colors=SLATE, labelsize=10.5)
    ax.grid(axis="y", color=RULE, lw=1, zorder=0)
    if note:
        ax.text(0, -0.16, note, transform=ax.transAxes, fontsize=8.5, color=MUTED, va="top")
    path = _save(fig, title)
    plt.close(fig)
    return path


# Ordered brand series colors for multi-series charts
_SERIES = [BLUE, SLATE, "#8FB0CC", "#9AA7B2", "#C2D0DC"]


def grouped_bar(title, categories, series: dict, ylabel: str = "", note: str = "",
                figsize=(9, 5)) -> str:
    """Grouped bar chart for comparing 2+ series across categories.

    series: ordered mapping of {series_name: [values aligned to categories]}.
    """
    plt, fig, ax = _new_axes(figsize)
    names  = list(series.keys())
    ncats  = len(categories)
    nser   = max(1, len(names))
    total  = 0.8
    width  = total / nser
    base   = [i - total / 2 + width / 2 for i in range(ncats)]
    for si, name in enumerate(names):
        xs = [b + si * width for b in base]
        ax.bar(xs, series[name], width=width * 0.95,
               color=_SERIES[si % len(_SERIES)], label=name, zorder=3)
    ax.set_xticks(range(ncats))
    ax.set_xticklabels([str(c) for c in categories])
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10.5, color=NAVY)
    ax.set_title(title, fontsize=14, fontweight="bold", color=NAVY, loc="left", pad=14)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(RULE)
    ax.tick_params(colors=SLATE, labelsize=10.5)
    ax.grid(axis="y", color=RULE, lw=1, zorder=0)
    ax.legend(frameon=False, fontsize=9.5, labelcolor=SLATE)
    if note:
        ax.text(0, -0.16, note, transform=ax.transAxes, fontsize=8.5, color=MUTED, va="top")
    path = _save(fig, title)
    plt.close(fig)
    return path


def trend_line(title, x, series: dict, ylabel: str = "", note: str = "",
               figsize=(9, 5)) -> str:
    """Line chart for trends over time. series: {name: [y aligned to x]}."""
    plt, fig, ax = _new_axes(figsize)
    for si, (name, ys) in enumerate(series.items()):
        ax.plot([str(v) for v in x], ys, marker="o", ms=5, lw=2.2,
                color=_SERIES[si % len(_SERIES)], label=name, zorder=3)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10.5, color=NAVY)
    ax.set_title(title, fontsize=14, fontweight="bold", color=NAVY, loc="left", pad=14)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(RULE)
    ax.tick_params(colors=SLATE, labelsize=10.5)
    ax.grid(axis="y", color=RULE, lw=1, zorder=0)
    if len(series) > 1:
        ax.legend(frameon=False, fontsize=9.5, labelcolor=SLATE)
    if note:
        ax.text(0, -0.16, note, transform=ax.transAxes, fontsize=8.5, color=MUTED, va="top")
    path = _save(fig, title)
    plt.close(fig)
    return path


def process_steps(title, steps, note: str = "", figsize=(10, 3.2)) -> str:
    """Horizontal numbered process diagram. `steps` is a list of (heading, detail)
    tuples (or plain strings). Renders numbered boxes joined by arrows."""
    import textwrap
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    plt, fig, ax = _new_axes(figsize)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
    ax.text(0, 96, title, fontsize=13.5, fontweight="bold", color=NAVY, va="top")

    norm = [(s if isinstance(s, (list, tuple)) else (s, "")) for s in steps]
    nstep = len(norm)
    gap = 2.5
    w = (100 - gap * (nstep - 1)) / nstep if nstep else 100
    for i, (head, detail) in enumerate(norm):
        x = i * (w + gap)
        ax.add_patch(FancyBboxPatch((x, 20), w, 52,
                     boxstyle="round,pad=0,rounding_size=2", fc="#EFF3F7", ec=BLUE, lw=2))
        ax.add_patch(plt.Circle((x + 3.6, 64), 2.6, color=BLUE, zorder=4))
        ax.text(x + 3.6, 64, str(i + 1), ha="center", va="center",
                color="white", fontsize=11, fontweight="bold", zorder=5)
        ax.text(x + 3, 54, "\n".join(textwrap.wrap(head, 18)),
                fontsize=10.3, fontweight="bold", color=NAVY, va="top")
        if detail:
            ax.text(x + 3, 38, "\n".join(textwrap.wrap(detail, 24)),
                    fontsize=8.8, color=SLATE, va="top")
        if i < nstep - 1:
            ax.add_patch(FancyArrowPatch((x + w + 0.2, 46), (x + w + gap - 0.2, 46),
                         arrowstyle="-|>", mutation_scale=15, color=GREY, lw=1.8))
    if note:
        ax.text(0, 8, note, fontsize=8.4, color=MUTED, va="top")
    path = _save(fig, title)
    plt.close(fig)
    return path
