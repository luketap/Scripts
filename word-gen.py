#!/usr/bin/env python3
"""
Generate all variants of a user-supplied string by:
  1) capitalization toggling
  2) common leetspeak substitutions
  3) optional numeric suffixes (length 1–4)

Includes a lightweight progress bar (no external deps).
"""

from __future__ import annotations

import argparse
import itertools
import sys
import time
from typing import Dict, Iterable, List


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
    for length in range(1, 5):
        for digits in itertools.product("0123456789", repeat=length):
            yield "".join(digits)


def iter_variants(s: str, subs: Dict[str, List[str]], append_digits: bool) -> Iterable[str]:
    if not append_digits:
        yield from iter_base_variants(s, subs)
        return

    for base in iter_base_variants(s, subs):
        for suffix in iter_digit_suffixes():
            yield f"{base}{suffix}"


def render_progress(done: int, total: int, start_time: float) -> None:
    if total <= 0:
        return

    width = 30
    pct = done / total
    filled = int(width * pct)
    bar = "=" * filled + "-" * (width - filled)

    elapsed = time.time() - start_time
    rate = done / elapsed if elapsed > 0 else 0

    msg = (
        f"\r[{bar}] "
        f"{pct:6.2%} "
        f"{done:,}/{total:,} "
        f"{rate:,.0f}/s"
    )
    sys.stderr.write(msg)
    sys.stderr.flush()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate capitalization + substitution variants with optional numeric suffixes."
    )
    ap.add_argument("text", nargs="?", help="Input string (prompted if omitted)")
    ap.add_argument(
        "-a", "--append-digits",
        action="store_true",
        help="Append all numeric combinations of length 1–4",
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
        help="Only print the total count (no generation)",
    )
    args = ap.parse_args()

    text = args.text
    if text is None:
        try:
            text = input("Enter string: ")
        except EOFError:
            return 1

    per_char = [options_for_char(ch, DEFAULT_SUBS) for ch in text]
    base_total = 1
    for opts in per_char:
        base_total *= len(opts)

    suffix_total = 11110 if args.append_digits else 1
    total = base_total * suffix_total

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

        for variant in iter_variants(text, DEFAULT_SUBS, args.append_digits):
            sink.write(variant + "\n")
            emitted += 1

            # Progress update every 1,000 items
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
