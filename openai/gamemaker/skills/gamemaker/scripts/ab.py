#!/usr/bin/env python3
"""Set up a blind A/B pair for one gamemaker polish round.

Copies the reference (the bar) and the candidate (our output) into
<round>/ab/A.<ext> and <round>/ab/B.<ext> in random order, normalising format
and size so the pair carries no tell about which is which, and writes the
answer key to <round>/ab/key.json.

The key must not be read until the verdict is committed to disk.
reveal.py enforces that ordering.

The pair is usually two filmstrips — the reference gameplay cut into frames
against our own scripted session cut the same way. A loop is visible in a
filmstrip and invisible in a single frame, which is why the play facet is
captured that way rather than as a screenshot.

Text artifacts (a design doc, a page of copy, a module) go through the same path:
formatting is normalised, because heading style and trailing whitespace identify
an author as reliably as a filename does. Blindness is weaker for text than for
images — you may simply recognise your own sentences — so for text the rubric
carries most of the weight and the A/B is a check on it. `--squint` on a
markdown pair emits a headings-only outline, which is the structural equivalent
of stepping back from a picture: it shows whether the document is shaped like
the bar before any sentence is read.

Usage:
  ab.py --round .gamemaker/<slug>/rounds/07 --ref .gamemaker/<slug>/ref/reference-strip.png \\
        --cand .gamemaker/<slug>/rounds/07/artifact.png [--shrink 1000] [--squint]
"""
from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".heic", ".bmp", ".gif"}
MARKDOWN_EXTS = {".md", ".markdown", ".mdx", ".txt", ".rst"}
TEXT_EXTS = MARKDOWN_EXTS | {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml",
    ".html", ".css", ".sh", ".sql", ".go", ".rs", ".c", ".h", ".cpp", ".java",
}
FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.S)
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$", re.M)


def has_sips() -> bool:
    return shutil.which("sips") is not None


def pixel_dims(path: Path) -> tuple[int, int] | None:
    if path.suffix.lower() not in IMAGE_EXTS or not has_sips():
        return None
    try:
        out = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
            check=True, capture_output=True, text=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None
    w = h = None
    for line in out.splitlines():
        try:
            if "pixelWidth:" in line:
                w = int(line.split(":")[1].strip())
            elif "pixelHeight:" in line:
                h = int(line.split(":")[1].strip())
        except ValueError:      # sips prints "<nil>" for anything it cannot decode
            return None
    return (w, h) if w and h else None


def normalise_text(body: str, markdown: bool) -> str:
    """Strip the incidental formatting that identifies an author rather than a quality."""
    body = body.replace("﻿", "").replace("\r\n", "\n").replace("\r", "\n")
    body = FRONTMATTER_RE.sub("", body)
    body = "\n".join(line.rstrip() for line in body.split("\n"))
    if markdown:
        body = re.sub(r"^[ \t]*[*+][ \t]+", "- ", body, flags=re.M)   # bullet style
        body = re.sub(r"^(#{1,6})[ \t]+(.+?)[ \t]*#+[ \t]*$", r"\1 \2", body, flags=re.M)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip() + "\n"


def normalise(src: Path, dst_stem: Path, shrink: int | None) -> Path:
    """Write src to dst_stem with a neutral format/size. Returns the written path."""
    ext = src.suffix.lower()
    if ext in IMAGE_EXTS and has_sips():
        dst = dst_stem.with_suffix(".png")
        cmd = ["sips", "-s", "format", "png"]
        if shrink:
            cmd += ["-Z", str(shrink)]
        cmd += [str(src), "--out", str(dst)]
        subprocess.run(cmd, check=True, capture_output=True)
        return dst
    if ext in TEXT_EXTS:
        try:
            body = src.read_text()
        except (UnicodeDecodeError, OSError):
            body = None
        if body is not None:
            dst = dst_stem.with_suffix(".md" if ext in MARKDOWN_EXTS else ext)
            dst.write_text(normalise_text(body, markdown=ext in MARKDOWN_EXTS))
            return dst
    dst = dst_stem.with_suffix(ext)
    shutil.copyfile(src, dst)
    return dst


def outline(path: Path) -> Path | None:
    """Headings plus per-section word counts — the squint test for a document.

    Shape is visible before prose is: a section the bar spends 400 words on and
    ours covers in 30 is a gap you can name without reading either.
    """
    if path.suffix.lower() not in MARKDOWN_EXTS | {".md"}:
        return None
    body = path.read_text(errors="replace")
    heads = list(HEADING_RE.finditer(body))
    if not heads:
        return None
    lines = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(body)
        words = len(body[m.end():end].split())
        lines.append(f"{'  ' * (len(m.group(1)) - 1)}{m.group(2)}  ({words}w)")
    dst = path.with_name(path.stem + ".outline.md")
    dst.write_text(f"{len(heads)} headings · {len(body.split())} words total\n\n"
                   + "\n".join(lines) + "\n")
    return dst


def squint(path: Path, size: int = 128) -> Path | None:
    """Heavily downscaled copy — the silhouette/first-impression test."""
    if path.suffix.lower() in MARKDOWN_EXTS:
        return outline(path)
    if path.suffix.lower() != ".png" or not has_sips():
        return None
    dst = path.with_name(path.stem + ".squint.png")
    subprocess.run(["sips", "-Z", str(size), str(path), "--out", str(dst)],
                   check=True, capture_output=True)
    return dst


def main() -> int:
    ap = argparse.ArgumentParser(description="Blind A/B pair for one gamemaker polish round")
    ap.add_argument("--round", required=True, help="round directory, e.g. .gamemaker/x/rounds/07")
    ap.add_argument("--ref", required=True, help="the bar: reference file to beat")
    ap.add_argument("--cand", required=True, help="our current output for this round")
    ap.add_argument("--shrink", type=int, default=1000,
                    help="max pixel dimension for images (0 = keep full size)")
    ap.add_argument("--squint", action="store_true",
                    help="also emit 128px versions for the silhouette test")
    args = ap.parse_args()

    ref, cand = Path(args.ref), Path(args.cand)
    for label, p in (("--ref", ref), ("--cand", cand)):
        if not p.is_file():
            print(f"error: {label} not found: {p}", file=sys.stderr)
            return 2

    ab_dir = Path(args.round) / "ab"
    ab_dir.mkdir(parents=True, exist_ok=True)
    for stale in ab_dir.glob("*"):
        stale.unlink()

    shrink = args.shrink or None
    if random.SystemRandom().random() < 0.5:
        assign = {"A": ("reference", ref), "B": ("candidate", cand)}
    else:
        assign = {"A": ("candidate", cand), "B": ("reference", ref)}

    written: dict[str, Path] = {}
    squints: dict[str, Path] = {}
    for side, (_role, src) in assign.items():
        written[side] = normalise(src, ab_dir / side, shrink)
        if args.squint:
            sq = squint(written[side])
            if sq:
                squints[side] = sq

    key = {
        "A": assign["A"][0],
        "B": assign["B"][0],
        "reference_source": str(ref),
        "candidate_source": str(cand),
        "shrink": shrink,
    }
    (ab_dir / "key.json").write_text(json.dumps(key, indent=2) + "\n")

    is_text = written["A"].suffix.lower() in TEXT_EXTS
    print(f"blind pair ready in {ab_dir}")
    print(f"  view (in this order): {written['A']}  {written['B']}")
    if squints:
        label = "outline first (structure before prose):" if is_text else "squint test first:"
        print(f"  {label} {squints.get('A', '-')}  {squints.get('B', '-')}")

    dr, dc = pixel_dims(written["A"]), pixel_dims(written["B"])
    if dr and dc:
        print(f"  A is {dr[0]}x{dr[1]}, B is {dc[0]}x{dc[1]}")
        ar_a, ar_b = dr[0] / dr[1], dc[0] / dc[1]
        if abs(ar_a - ar_b) / max(ar_a, ar_b) > 0.05:
            print("  WARNING: aspect ratios differ — that is a tell, and it also means you are "
                  "not comparing like with like. Match the capture framing to the reference.")
    elif is_text:
        wa = len(written["A"].read_text(errors="replace").split())
        wb = len(written["B"].read_text(errors="replace").split())
        print(f"  A is {wa} words, B is {wb} words")
        if max(wa, wb) and min(wa, wb) / max(wa, wb) < 0.6:
            print("  WARNING: the two sides differ in length by more than 40% — that is a tell, "
                  "and length is not the quality being judged. Compare like with like: pit one "
                  "section against the matching section rather than whole documents.")
        print("  Note: blindness is weak for text you wrote yourself. Score the rubric line by "
              "line and let that verdict stand even if you think you recognise a side.")

    print("\n  Now: score both sides against RUBRIC.md, write the verdict, THEN run reveal.py.")
    print("  Do not open key.json yourself — reveal.py checks the verdict exists first.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
