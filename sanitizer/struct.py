"""
Helpers for Stage-2 structural & metadata scans.
"""
from __future__ import annotations
import re, pathlib
import pdfplumber, pikepdf
from . import TRIGGERS

RX = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in TRIGGERS]


def pdf_hidden_chars(path: pathlib.Path) -> int:
    """Count chars that are likely invisible (white fill or tiny font)."""
    hidden = 0
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            for char in page.chars:
                size = char.get("size", 12)
                color = char.get("non_stroking_color", None)
                # pdfplumber represents white as 1-tuple (1.0,) or 3-tuple (1,1,1)
                is_white = color in {(1,), (1, 1, 1)}
                if is_white or size <= 1:
                    hidden += 1
    return hidden


def pdf_meta_hits(path: pathlib.Path) -> list[str]:
    """Return list of trigger patterns that match any PDF metadata field."""
    hits: list[str] = []
    with pikepdf.open(str(path)) as pdf:
        info = pdf.docinfo  # may be pikepdf.Dictionary or pikepdf.Object

        # Robustly build one big string from the metadata object
        if hasattr(info, "items"):                     # most versions
            meta_text = " ".join(str(v) for _, v in info.items())
        else:                                         # fall-back
            meta_text = str(info)

        for rx in RX:
            if rx.search(meta_text):
                hits.append(rx.pattern)
    return hits
