#!/usr/bin/env python3
"""Render a Digimon-inspired contribution calendar as light and dark SVGs."""

from __future__ import annotations

import argparse
import html
import re
import urllib.request
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path


class ContributionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.days: dict[date, tuple[int, int]] = {}
        self.ids: dict[str, date] = {}
        self.tooltip_for: str | None = None
        self.tooltip_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "tool-tip" and data.get("for"):
            self.tooltip_for = data["for"]
            self.tooltip_text = ""
            return
        if tag != "td":
            return
        day_text = data.get("data-date")
        if not day_text:
            return
        try:
            day = date.fromisoformat(day_text)
        except ValueError:
            return
        level_text = data.get("data-level", "0") or "0"
        level = int(level_text) if level_text.isdigit() else 0
        self.days[day] = (0, max(0, min(4, level)))
        if data.get("id"):
            self.ids[data["id"]] = day

    def handle_data(self, data: str) -> None:
        if self.tooltip_for:
            self.tooltip_text += data

    def handle_endtag(self, tag: str) -> None:
        if tag != "tool-tip" or not self.tooltip_for:
            return
        day = self.ids.get(self.tooltip_for)
        if day:
            match = re.search(r"(\d+) contributions?", self.tooltip_text)
            count = int(match.group(1)) if match else 0
            _, level = self.days[day]
            self.days[day] = (count, level)
        self.tooltip_for = None
        self.tooltip_text = ""


PALETTES = {
    "light": {
        "background": "#ffffff",
        "text": "#1f2328",
        "muted": "#59636e",
        "grid": ["#ebedf0", "#c6e48b", "#7bc96f", "#239a3b", "#196127"],
        "outline": "#452b22",
    },
    "dark": {
        "background": "#0d1117",
        "text": "#e6edf3",
        "muted": "#9198a1",
        "grid": ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"],
        "outline": "#402a23",
    },
}


def fetch_contributions(username: str) -> dict[date, tuple[int, int]]:
    url = f"https://github.com/users/{username}/contributions"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "digimon-contribution-graph/1.0", "Accept": "text/html"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8", errors="replace")
    parser = ContributionParser()
    parser.feed(page)
    if not parser.days:
        raise RuntimeError("GitHub returned no contribution calendar cells.")
    return parser.days


def draw_digimon(x: int, y: int) -> str:
    # Compact vector fan-art cues: Gabumon's pale pelt, blue stripes, horn, and yellow belly.
    return f"""
      <g class="monster" transform="translate({x} {y}) scale(2)">
        <!-- striped pelt and body -->
        <path d="M5 9 2 7 3 5 6 6 8 4 12 5 15 7 18 7 20 10 19 14 17 15 16 19 13 19 12 16 9 16 8 19 5 19 5 16 3 15 4 12 2 11Z" fill="#e8eef8" stroke="#26325c" stroke-width=".8" stroke-linejoin="round"/>
        <!-- tail, forelegs, paws -->
        <path d="m5 13-3-1-2 2 1 3 4-1M7 14l-1 4h3l1-3m4-1 1 4h3l-1-5" fill="#dce5f3" stroke="#26325c" stroke-width=".8" stroke-linejoin="round"/>
        <path d="m6 18-1 2h4l1-2m3 0 1 2h4l-1-2" fill="#f4f5fa" stroke="#26325c" stroke-width=".6" stroke-linejoin="round"/>
        <!-- blue pelt stripes and head marking -->
        <path d="m4 8 3 1-1 2-3-1m5-4 2 1-1 3-2-1m7-1 2 1-1 3-2-1m4 0 2 1-1 2-2-1m-9 3 3 1-1 2-3-1m7-2 2 1-1 2-2-1" fill="#3853a4"/>
        <path d="M8 6 10 4l2 1 2 2-2 2H9Z" fill="#314b9a"/>
        <!-- head, muzzle, eyes, and horn -->
        <path d="m7 9 1-3 3-2 4 1 2 3 2 1-1 3-3 1-2-1-3 1-3-2Z" fill="#f4f5fa" stroke="#26325c" stroke-width=".8" stroke-linejoin="round"/>
        <path d="m10 3 1-3h2l1 4-1 2h-2Z" fill="#f4cf36" stroke="#85651b" stroke-width=".6" stroke-linejoin="round"/>
        <path d="M8 8 5 6 4 8l3 2m8-3 3-2 1 2-3 2" fill="#dce5f3" stroke="#26325c" stroke-width=".7" stroke-linejoin="round"/>
        <path d="M9 8h2v2H9zM14 8h2v2h-2z" fill="#a9273e"/>
        <path d="M10 8h1v1h-1zM15 8h1v1h-1z" fill="#111827"/>
        <path d="m8 11 2-1h5l2 2-2 2h-5l-2-1Z" fill="#f4f5fa" stroke="#26325c" stroke-width=".6" stroke-linejoin="round"/>
        <path d="m9 11 1 2 1-2m1 0 1 2 1-2" fill="#ffffff"/>
        <path d="M11 12h2v1h-2z" fill="#18213e"/>
        <!-- golden belly and claws -->
        <path d="m9 13 2 1h3l1 2-2 1h-4l-1-2Z" fill="#f4d74b" stroke="#a17d20" stroke-width=".4"/>
        <path d="m5 19 1-1 1 2m2 0 1-2 1 2m3 0 1-2 1 2m1 0 1-2 1 2" fill="none" stroke="#6d4c9a" stroke-width=".8" stroke-linecap="round"/>
      </g>"""


def render_svg(days: dict[date, tuple[int, int]], theme: str, username: str) -> str:
    palette = PALETTES[theme]
    colors = palette["grid"]
    first_day = min(days)
    start = first_day - timedelta(days=(first_day.weekday() + 1) % 7)
    cell = 12
    gap = 4
    pitch = cell + gap
    x0 = 76
    y0 = 92
    graph_width = 53 * pitch - gap
    width = x0 + graph_width + 38
    height = 236

    rects: list[str] = []
    months: list[str] = []
    previous_month: tuple[int, int] | None = None
    total = 0
    for offset in range(371):
        day = start + timedelta(days=offset)
        week = offset // 7
        row = offset % 7
        count, level = days.get(day, (0, 0))
        total += count
        x = x0 + week * pitch
        y = y0 + row * pitch
        rects.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" '
            f'fill="{colors[level]}" data-date="{day.isoformat()}" data-count="{count}"/>'
        )
        current_month = (day.year, day.month)
        if day.day == 1 and current_month != previous_month:
            months.append(
                f'<text x="{x}" y="68" class="month">{day.strftime("%b")}</text>'
            )
        previous_month = current_month

    safe_user = html.escape(username)
    travel = graph_width - 58
    cells = "\n".join(rects)
    month_labels = "\n".join(months)
    mascot = draw_digimon(0, 0)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">
  <title id="title">Gabumon contribution field for {safe_user}</title>
  <desc id="description">A small Gabumon-inspired character travels across a contribution calendar with {total} contributions in the displayed year.</desc>
  <style>
    .bg {{ fill: {palette['background']}; }}
    .title {{ fill: {palette['text']}; font: 700 16px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif; }}
    .subtitle {{ fill: {palette['muted']}; font: 12px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif; }}
    .month {{ fill: {palette['muted']}; font: 10px -apple-system,BlinkMacSystemFont,Segoe UI,sans-serif; }}
    .runner {{ transform-box: view-box; transform-origin: 0 0; animation: travel 18s linear infinite alternate; }}
    .monster {{ animation: bob .32s steps(2,end) infinite alternate; }}
    @keyframes travel {{ from {{ transform: translateX(0); }} to {{ transform: translateX({travel}px); }} }}
    @keyframes bob {{ from {{ translate: 0 0; }} to {{ translate: 0 -2px; }} }}
    @media (prefers-reduced-motion: reduce) {{ .runner, .monster {{ animation: none; }} }}
  </style>
  <rect class="bg" width="100%" height="100%" rx="14"/>
  <text x="24" y="31" class="title">GABUMON · CONTRIBUTION FIELD</text>
  <text x="24" y="50" class="subtitle">{safe_user} · {total} contributions this year</text>
  {month_labels}
  <g aria-label="Contribution calendar">{cells}</g>
  <g transform="translate({x0} 82)"><g class="runner">{mascot}</g></g>
  <g transform="translate({x0} 221)">
    <text x="0" y="0" class="month">Less</text>
    <rect x="34" y="-10" width="12" height="12" rx="3" fill="{colors[0]}"/>
    <rect x="51" y="-10" width="12" height="12" rx="3" fill="{colors[1]}"/>
    <rect x="68" y="-10" width="12" height="12" rx="3" fill="{colors[2]}"/>
    <rect x="85" y="-10" width="12" height="12" rx="3" fill="{colors[3]}"/>
    <rect x="102" y="-10" width="12" height="12" rx="3" fill="{colors[4]}"/>
    <text x="122" y="0" class="month">More</text>
  </g>
</svg>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True)
    parser.add_argument("--output-dir", default="dist")
    args = parser.parse_args()

    contributions = fetch_contributions(args.username)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        path = output / f"digimon-contribution-graph{'-dark' if theme == 'dark' else ''}.svg"
        path.write_text(render_svg(contributions, theme, args.username), encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
