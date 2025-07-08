"""
sanitize — CLI to scan papers for LLM prompt injections
• Strips prompt-injection triggers
• Detects hidden text & metadata tricks
• Emits event-level JSON + optional diff

Default outputs:
    <input_stem>_clean.txt
    <input_stem>_clean.json
"""

from __future__ import annotations

import argparse
import datetime as _dt
import difflib
import json
import pathlib
import re
import sys
from typing import Dict, List, Tuple

from . import TRIGGERS
from .struct import pdf_hidden_chars, pdf_meta_hits

# ----------------------------------------------------------------------
_PATTERNS: List[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE | re.DOTALL) for p in TRIGGERS
]


def _extract_text(path: pathlib.Path) -> str:
    if path.suffix.lower() in {".tex", ".txt"}:
        return path.read_text(errors="ignore")

    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        sys.exit("pdfminer.six is required for PDF input — `pip install pdfminer.six`")

    return extract_text(path)


def _sanitize_events(text: str) -> Tuple[str, List[Dict]]:
    """
    Remove patterns while collecting per-match events.
    Each event dict → {'type': 'regex', 'expr': pattern, 'start': idx, 'end': idx}
    """
    events: List[Dict] = []
    for rx in _PATTERNS:
        for m in rx.finditer(text):
            events.append(
                {
                    "type": "regex",
                    "expr": rx.pattern,
                    "start": m.start(),
                    "end": m.end(),
                    "snippet": m.group(0)[:100],
                }
            )
        text = rx.sub("", text)
    return text, events


# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sanitize",
        description="Strip prompt-injection triggers from papers and score risk.",
    )
    parser.add_argument("file", type=pathlib.Path, help="PDF, LaTeX or plain-text file")
    parser.add_argument(
        "-o",
        "--out",
        type=pathlib.Path,
        default=None,
        help="Destination text file (default: <input>_clean.txt)",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Print word-level diff between original and clean text",
    )
    args = parser.parse_args()

    # ---------- Prepare filenames ----------
    if args.out is None:
        out_txt = args.file.with_stem(f"{args.file.stem}_clean").with_suffix(".txt")
    else:
        out_txt = args.out
    out_json = out_txt.with_suffix(".json")

    # ---------- Stage-1 regex firewall with events ----------
    raw_text = _extract_text(args.file)
    clean_text, events = _sanitize_events(raw_text)

    # ---------- Stage-2 structural scan ----------
    hidden_chars = 0
    meta_hits: List[str] = []
    if args.file.suffix.lower() == ".pdf":
        hidden_chars = pdf_hidden_chars(args.file)
        if hidden_chars:
            events.append({"type": "hidden_text", "chars": hidden_chars})
        meta_hits = pdf_meta_hits(args.file)
        for pat in meta_hits:
            events.append({"type": "metadata", "expr": pat})

    # ---------- Risk score ----------
    risk_num = len([e for e in events if e["type"] == "regex"]) + hidden_chars / 100 + len(
        meta_hits
    ) * 0.5
    if risk_num < 1.5:
        risk_level = "low"
    elif risk_num < 4:
        risk_level = "medium"
    else:
        risk_level = "high"

    # ---------- Write outputs ----------
    out_txt.write_text(clean_text)
    report = {
        "timestamp": _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "file": args.file.name,
        "out_text": str(out_txt),
        "risk": round(risk_num, 2),
        "risk_level": risk_level,
        "events": events,
    }
    out_json.write_text(json.dumps(report, indent=2))

    # ---------- Console summary ----------
    print("───────── Analysis Summary ─────────")
    print(f"Input file       : {args.file}")
    print(f"Clean text saved : {out_txt}")
    print(f"Report JSON      : {out_json}")
    print(f"Risk             : {report['risk']}  ({risk_level.upper()})\n")

    if events:
        print("Events:")
        for ev in events:
            if ev["type"] == "regex":
                print(f"  • regex  {ev['expr']!r}  @ {ev['start']}–{ev['end']}")
            elif ev["type"] == "hidden_text":
                print(f"  • hidden_text  {ev['chars']} chars")
            elif ev["type"] == "metadata":
                print(f"  • metadata hit {ev['expr']!r}")
    else:
        print("No suspicious content found.")

    # ---------- Optional diff ----------
    if args.diff:
        print("\n───────── Diff (clean vs. original) ─────────")
        for line in difflib.unified_diff(
            raw_text.split(), clean_text.split(), lineterm=""
        ):
            print(line)

    print("───────── Done ─────────")


if __name__ == "__main__":
    main()