#!/usr/bin/env python3
"""
Wordlist Generator v1.1

A high-performance wordlist generation utility designed for password auditing and
security testing. The tool expands a base string into realistic permutations by applying:

  - Uppercase and lowercase variations
  - Common leetspeak and symbol substitutions
  - Optional numeric suffixes of length 1–4 (e.g. 7, 22, 0022)
  - Optional year suffixes from a range (e.g. 1970–2026), with optional 2-digit years

Generation is streamed, memory-safe, and suitable for very large outputs. Progress is
displayed in real time without polluting stdout, making the tool safe for piping and
file redirection.
"""

from __future__ import annotations

import argparse
import itertools
import sys
import time
from typing import Dict, Iterable, List, Tuple


VERSION = "v1.1"

BANNER = rf"""
 __      __                .___            ________
/  \    /  \___________  __| _/           /  _____/  ____   ____
\   \/\/   /  _ \_  __ \/ __ |    ______  /   \  ___ / __ \ /    \
 \        (  <_> )  | \/ /_/ |   /_____/  \    \_\  \  ___/|   |  \
  \__/\  / \____/|__|  \____ |              \______  /\___  >___|  /
       \/                   \/                     \/     \/     \/


  Wordlist Generator {VERSION}

  Author: Wir3Tap

"""

DEFAULT_SUBS: Dict[str, List[str]] = {
    "a": ["a", "A", "@", "4"],
    "b": ["b", "B", "8"],
    "c": ["c", "C", "("],
    "e": ["e", "E", "3"],
    "g": ["g", "G", "9", "6"],
    "i": ["i", "I", "1", "!"],
    "l": ["l", "L", "1", "|"],
    "o": ["o", "O", "0"],
    "s": ["s", "S", "$", "5"],
    "t": ["t", "T", "7", "+"],
    "z": ["z", "Z", "2"],
}


def options_for_char(ch: str, subs: Dict[str, List[str]]) -> List[str]:
    if ch.isalpha():
        key = ch.lower()
        opts = subs[key] if key in subs else [ch.lower(), ch.upper()]
    else:
        opts = [ch]

    # Deduplicate while preserving order
    seen = set()
    out: List[str] = []
    for o in opts:
        if o not in seen:
            seen.add(o)
            out.append(o)
    return out


def iter_base_variants(s: str, subs: Dict[str, List[str]]) -> Iterable[str]:
    per_char = [options_for_char(ch, subs) for ch in s]
    for combo in itertools.product(*per_char):
        yield "".join(combo)


def iter_digit_suffixes() -> Iterable[str]:
    """All digit strings of length 1–4, including leading-zero variants (total 11,110)."""
    for length in range(1, 5):
        for digits in itertools.product("0123456789", repeat=length):
            yield "".join(digits)


def parse_year_range(spec: str) -> Tuple[int, int]:
    """
    Parse 'START-END' into ints. If reversed, normalize to ascending.
    Raises ValueError on bad format.
    """
    try:
        a, b = spec.split("-", 1)
        start = int(a.strip())
        end = int(b.strip())
        if start > end:
            start, end = end, start
        return start, end
    except Exception as e:
        raise ValueError("Invalid --years format. Use START-END (e.g. 1970-2026).") from e


def iter_year_suffixes(years_spec: str, year2: bool) -> Iterable[str]:
    """Yield year suffixes for a range, optionally also yielding 2-digit years."""
    if not years_spec:
        return
        yield  # pragma: no cover (keeps type checkers happy)

    start, end = parse_year_range(years_spec)
    for y in range(start, end + 1):
        yield str(y)
        if year2:
            yield f"{y % 100:02d}"


def iter_variants(
    s: str,
    subs: Dict[str, List[str]],
    append_digits: bool,
    years_spec: str,
    year2: bool,
) -> Iterable[str]:
    """
    Generate:
      - base variants
      - optionally base+year suffixes
      - optionally base+digit suffixes (1–4 digits)
    """
    no_suffixes = (not append_digits) and (not years_spec)

    for base in iter_base_variants(s, subs):
        if no_suffixes:
            yield base
            continue

        if years_spec:
            for ys in iter_year_suffixes(years_spec, year2):
                yield f"{base}{ys}"

        if append_digits:
            for ds in iter_digit_suffixes():
                yield f"{base}{ds}"


def render_progress(done: int, total: int, start_time: float) -> None:
    if total <= 0:
        return

    width = 30
    pct = done / total
    filled = int(width * pct)
    bar = "=" * filled + "-" * (width - filled)

    elapsed = time.time() - start_time
    rate = done / elapsed if elapsed > 0 else 0

    sys.stderr.write(f"\r[{bar}] {pct:6.2%} {done:,}/{total:,} {rate:,.0f}/s")
    sys.stderr.flush()


def main() -> int:
    sys.stderr.write(BANNER + "\n")

    ap = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=(
            "\n"
            "Generate realistic password wordlists by expanding a base string "
            "with capitalization, common character substitutions, and optional "
            "numeric or year-based suffix expansion.\n"
            "Designed for security testing, password auditing, and controlled "
            "credential recovery workflows."
            "\n"
        )
    )
    ap.add_argument("text", nargs="?", help="Base input string (prompted if omitted)")
    ap.add_argument(
        "-a", "--append-digits",
        action="store_true",
        help="Append all numeric combinations of length 1–4 (e.g. 7, 22, 0022)",
    )
    ap.add_argument(
        "-y", "--years",
        default="",
        help="Append year suffixes from a range, e.g. 1970-2026",
    )
    ap.add_argument(
        "--year2",
        action="store_true",
        help="Also append 2-digit years when using --years (e.g. 70..26)",
    )
    ap.add_argument(
        "-l", "--limit",
        type=int,
        default=0,
        help="Stop after emitting this many variants (0 = no limit)",
    )
    ap.add_argument(
        "-o", "--out",
        default="",
        help="Write results to a file instead of stdout",
    )
    ap.add_argument(
        "-c", "--count-only",
        action="store_true",
        help="Only print the total count without generating the wordlist",
    )
    args = ap.parse_args()

    text = args.text
    if text is None:
        try:
            text = input("Enter base string: ")
        except EOFError:
            return 1

    # Count base variants
    per_char = [options_for_char(ch, DEFAULT_SUBS) for ch in text]
    base_total = 1
    for opts in per_char:
        base_total *= len(opts)

    # Count year suffixes
    year_total = 1
    if args.years:
        y0, y1 = parse_year_range(args.years)
        year_total = (y1 - y0 + 1) * (2 if args.year2 else 1)

    # Count digit suffixes
    digit_total = 11110 if args.append_digits else 1

    total = base_total * year_total * digit_total
    if args.limit:
        total = min(total, args.limit)

    if args.count_only:
        print(total)
        return 0

    out_fh = None
    try:
        sink = sys.stdout
        if args.out:
            out_fh = open(args.out, "w", encoding="utf-8", newline="\n")
            sink = out_fh

        emitted = 0
        start = time.time()
        last_update = 0

        for variant in iter_variants(text, DEFAULT_SUBS, args.append_digits, args.years, args.year2):
            sink.write(variant + "\n")
            emitted += 1

            if emitted - last_update >= 1000:
                render_progress(emitted, total, start)
                last_update = emitted

            if args.limit and emitted >= args.limit:
                break

        render_progress(emitted, total, start)
        sys.stderr.write("\n")

        if out_fh:
            print(f"Wrote {emitted} variants to {args.out}")
        return 0
    finally:
        if out_fh:
            out_fh.close()


if __name__ == "__main__":
    raise SystemExit(main())
