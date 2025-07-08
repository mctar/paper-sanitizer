import argparse, pathlib, re, sys
from . import TRIGGERS

PATTERNS = [re.compile(p, re.DOTALL) for p in TRIGGERS]  # DOTALL → .* spans lines


def extract_text(path: pathlib.Path) -> str:
    """Return plain text from .pdf, .tex or .txt."""
    if path.suffix.lower() in {".tex", ".txt"}:
        return path.read_text(errors="ignore")

    try:
        from pdfminer.high_level import extract_text
    except ImportError:
        sys.exit("pdfminer.six missing – run `pip install pdfminer.six`")

    return extract_text(path)


def sanitize(text: str):
    """Strip triggers; return (clean_text, list_of_removed_segments)."""
    removed = []
    for rx in PATTERNS:
        text, n = rx.subn("", text)
        if n:
            removed.append((rx.pattern, n))
    return text, removed


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="sanitize",
        description="Strip prompt-injection triggers from papers.",
    )
    ap.add_argument("file", type=pathlib.Path, help="PDF, LaTeX or plain-text file")
    ap.add_argument(
        "-o", "--out", type=pathlib.Path, default="clean.txt",
        help="Destination text file (default: clean.txt)",
    )
    args = ap.parse_args()

    raw = extract_text(args.file)
    clean, hits = sanitize(raw)
    args.out.write_text(clean)
    print(f"✔ Clean text saved → {args.out}")

    if hits:
        print("\nRemoved segments:")
        for pattern, n in hits:
            print(f"  • {pattern!r}  ×{n}")
    else:
        print("No trigger patterns found.")


if __name__ == "__main__":
    main()
