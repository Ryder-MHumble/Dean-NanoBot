#!/usr/bin/env python3
"""
Nanobot API Usage Dashboard
Usage: python3 api_dash.py [-i SECONDS]
"""

import json
import os
import sys
import time
import signal
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

USAGE_FILE = Path.home() / ".nanobot" / "usage.jsonl"

# ── ANSI palette (matches deploy.sh / monitor.sh) ─────────────
R    = '\033[0;31m'
G    = '\033[0;32m'
Y    = '\033[0;33m'
C    = '\033[0;36m'
D    = '\033[0;90m'
BOLD = '\033[1m'
NC   = '\033[0m'
BW   = '\033[1;97m'
P1   = '\033[38;5;57m'
P2   = '\033[38;5;63m'
P3   = '\033[38;5;69m'
P4   = '\033[38;5;75m'
P5   = '\033[38;5;81m'
P6   = '\033[38;5;87m'


# ── Data helpers ──────────────────────────────────────────────

def load_records() -> list[dict]:
    if not USAGE_FILE.exists():
        return []
    records = []
    with open(USAGE_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records


def compute_stats(records: list[dict], since: datetime | None = None) -> dict:
    s = {"calls": 0, "in": 0, "out": 0, "total": 0, "cost": 0.0}
    for r in records:
        try:
            ts = datetime.fromisoformat(r["ts"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if since and ts < since:
                continue
        except (KeyError, ValueError):
            continue
        s["calls"] += 1
        s["in"]    += r.get("in", 0)
        s["out"]   += r.get("out", 0)
        s["total"] += r.get("total", 0)
        s["cost"]  += r.get("cost", 0.0)
    return s


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def fmt_cost(c: float) -> str:
    if c == 0:
        return "$0.0000"
    if c < 0.0001:
        return f"${c:.6f}"
    return f"${c:.4f}"


def short_model(model: str) -> str:
    """Strip provider prefix for display (openrouter/anthropic/claude-3 → claude-3)."""
    parts = model.split("/")
    display = "/".join(parts[-2:]) if len(parts) >= 2 else model
    return display[:28]


def compute_user_stats(records: list[dict], since: datetime | None = None) -> list[dict]:
    """Aggregate usage grouped by (sender, channel), sorted by total tokens desc."""
    buckets: dict[tuple[str, str], dict] = {}
    for r in records:
        try:
            ts = datetime.fromisoformat(r["ts"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if since and ts < since:
                continue
        except (KeyError, ValueError):
            continue
        key = (r.get("sender", "unknown"), r.get("channel", "unknown"))
        if key not in buckets:
            buckets[key] = {"sender": key[0], "channel": key[1],
                            "calls": 0, "in": 0, "out": 0, "total": 0, "cost": 0.0}
        b = buckets[key]
        b["calls"] += 1
        b["in"]    += r.get("in", 0)
        b["out"]   += r.get("out", 0)
        b["total"] += r.get("total", 0)
        b["cost"]  += r.get("cost", 0.0)
    return sorted(buckets.values(), key=lambda x: x["total"], reverse=True)


# ── Render ────────────────────────────────────────────────────

W = 70  # display width


def hr(char="─"):
    print(f"  {D}{char * W}{NC}")


def render(interval: int) -> None:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start  = now - timedelta(days=7)

    records    = load_records()
    today      = compute_stats(records, since=today_start)
    week       = compute_stats(records, since=week_start)
    alltime    = compute_stats(records)
    user_stats = compute_user_stats(records)          # all-time, per user
    recent     = sorted(records, key=lambda r: r.get("ts", ""), reverse=True)[:10]

    # ── Banner ────────────────────────────────────────────────
    print()
    print(f"  {P1}{BOLD}███╗  ██╗ █████╗ ███╗  ██╗  ██████╗  ██████╗ ████████╗{NC}")
    print(f"  {P2}{BOLD}████╗ ██║██╔══██╗████╗ ██║ ██╔═══██╗██╔═══██╗╚══██╔══╝{NC}")
    print(f"  {P3}{BOLD}██╔████╔╝███████║██╔████╔╝ ██║   ██║██║   ██║   ██║   {NC}")
    print(f"  {P4}{BOLD}██║╚████║██╔══██║██║╚████║ ██║   ██║██║   ██║   ██║   {NC}")
    print(f"  {P5}{BOLD}██║ ╚███║██║  ██║██║ ╚███║ ╚██████╔╝╚██████╔╝   ██║   {NC}")
    print(f"  {P6}{BOLD}╚═╝  ╚══╝╚═╝  ╚═╝╚═╝  ╚══╝  ╚═════╝  ╚═════╝   ╚═╝   {NC}")
    print(f"  {P4}{BOLD}A P I   U S A G E{NC}")
    print()

    # ── Summary table ─────────────────────────────────────────
    print(f"  {P3}{'═' * W}{NC}")
    print(f"  {BOLD}{'':8}{'TODAY':>18}{'LAST 7 DAYS':>18}{'ALL TIME':>18}{NC}")
    hr()

    rows = [
        ("CALLS",  lambda s: str(s["calls"]),        D),
        ("INPUT",  lambda s: fmt_tokens(s["in"]),    C),
        ("OUTPUT", lambda s: fmt_tokens(s["out"]),   G),
        ("TOTAL",  lambda s: fmt_tokens(s["total"]), BW),
        ("COST",   lambda s: fmt_cost(s["cost"]),    Y),
    ]
    for label, fn, color in rows:
        vals = [fn(today), fn(week), fn(alltime)]
        print(f"  {D}{label:<8}{NC}", end="")
        for v in vals:
            print(f"{color}{v:>18}{NC}", end="")
        print()

    # ── Per-user breakdown ────────────────────────────────────
    print(f"\n  {P3}{'═' * W}{NC}")
    print(f"  {BOLD}USAGE BY USER  {D}(all time, sorted by tokens){NC}")
    hr()

    if not user_stats:
        print(f"  {D}No data yet — sender field available after next deploy.{NC}")
    else:
        print(f"  {D}{'SENDER':<22}{'CH':<10}{'CALLS':>6}{'INPUT':>9}{'OUTPUT':>9}{'TOTAL':>9}{'COST':>10}{NC}")
        hr("·")
        for u in user_stats[:12]:  # cap at 12 rows
            sender  = str(u["sender"])[:20]
            channel = str(u["channel"])[:8]
            calls   = str(u["calls"])
            in_t    = fmt_tokens(u["in"])
            out_t   = fmt_tokens(u["out"])
            total_t = fmt_tokens(u["total"])
            cost    = fmt_cost(u["cost"])
            print(f"  {BW}{sender:<22}{NC}{D}{channel:<10}{NC}"
                  f"{D}{calls:>6}{NC}{C}{in_t:>9}{NC}{G}{out_t:>9}{NC}"
                  f"{BW}{total_t:>9}{NC}{Y}{cost:>10}{NC}")

    # ── Recent calls ──────────────────────────────────────────
    print(f"\n  {P3}{'═' * W}{NC}")
    print(f"  {BOLD}RECENT CALLS{NC}")
    hr()

    if not recent:
        print(f"  {D}No API calls recorded yet.{NC}")
    else:
        print(f"  {D}{'TIME':<9}{'SENDER':<16}{'MODEL':<22}{'IN':>7}{'OUT':>7}{'COST':>9}{NC}")
        hr("·")
        for r in recent:
            try:
                ts_str = datetime.fromisoformat(r["ts"]).strftime("%H:%M:%S")
            except (KeyError, ValueError):
                ts_str = "?"
            sender = str(r.get("sender", "?"))[:14]
            model  = short_model(r.get("model", "?"))
            in_t   = fmt_tokens(r.get("in", 0))
            out_t  = fmt_tokens(r.get("out", 0))
            cost   = fmt_cost(r.get("cost", 0.0))
            print(f"  {D}{ts_str:<9}{NC}{BW}{sender:<16}{NC}{model:<22}"
                  f"{C}{in_t:>7}{NC}{G}{out_t:>7}{NC}{Y}{cost:>9}{NC}")

    print(f"  {P3}{'═' * W}{NC}")

    # ── Footer ────────────────────────────────────────────────
    local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n  {D}File   {USAGE_FILE}{NC}")
    print(f"  {D}Time   {local_time}   Refresh: {interval}s   Press Ctrl+C to quit{NC}\n")


# ── Main loop ─────────────────────────────────────────────────

def cleanup(signum=None, frame=None):
    # Show cursor, reset terminal
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()
    print(f"\n{G}Dashboard stopped.{NC}")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Nanobot API Usage Dashboard")
    parser.add_argument("-i", "--interval", type=int, default=5,
                        help="Refresh interval in seconds (default: 5)")
    args = parser.parse_args()

    signal.signal(signal.SIGINT,  cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Hide cursor
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

    try:
        # Clear screen once
        os.system("clear" if os.name == "posix" else "cls")

        while True:
            # Move cursor to top-left (no full clear = no flicker)
            sys.stdout.write("\033[H")
            sys.stdout.flush()

            render(args.interval)

            # Erase from cursor to end of screen (clear leftover lines)
            sys.stdout.write("\033[J")
            sys.stdout.flush()

            time.sleep(args.interval)

    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
