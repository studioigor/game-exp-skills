#!/usr/bin/env python3
"""Prove the harness, mechanically. Stage 2 does not close on a claim.

Runs the frozen SESSION command twice with the same seed and checks what a
whole unattended run depends on: files actually appear, the metrics JSON
parses and carries the required keys, the session reports completed, two
identical seeds produce identical gameplay metrics (fps and wall-clock are
allowed to vary — the dice are not), the SCREENSHOT command yields an image,
and ab.py can build a blind pair from it.

On a full pass it flips `CAPTURE PROVEN: yes` in HARNESS.md itself — that
line is not written by hand — and adds the proven commands to the project's
`.claude/settings.local.json` allowlist, because a permission prompt at round
12 kills an unattended run as surely as a broken capture does.

Usage:
  preflight.py .gamemaker/<slug>
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from next import field, read, PLACEHOLDER  # noqa: E402

REQUIRED_KEYS = ["completed", "duration", "fps_mean", "events"]
# Allowed to differ between two same-seed runs: they measure the machine, not the game.
VOLATILE = {"duration", "fps_mean", "fps_min", "fps_samples", "input_latency_ms", "ts"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
COMMANDS = ["SESSION", "SCREENSHOT", "FIRST SESSION", "PERF", "SOAK"]

failures: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> bool:
    print(f"  {'ok ' if ok else 'FAIL'}  {label}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(label + (f": {detail}" if detail else ""))
    return ok


def rewrite_out(cmd: str, out: Path) -> str | None:
    """Point the command's --out at our directory, so two runs can be compared."""
    new, n = re.subn(r"(--out[=\s]+)(\S+)", rf"\g<1>{out}", cmd, count=1)
    return new if n else None


def run(cmd: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=900)


def newest(root: Path, name_glob: str, after: float, exclude: Path) -> Path | None:
    hits = [p for p in root.rglob(name_glob)
            if p.stat().st_mtime >= after and exclude not in p.parents]
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def session_once(cmd: str, root: Path, out: Path) -> dict | None:
    """Run the SESSION command once; return its parsed metrics or None."""
    out.mkdir(parents=True, exist_ok=True)
    redirected = rewrite_out(cmd, out)
    t0 = time.time()
    proc = run(redirected or cmd, root)
    if not check(proc.returncode == 0, "SESSION exits 0",
                 (proc.stderr or proc.stdout).strip()[-300:]):
        return None
    mfile = (out / "metrics.json") if redirected and (out / "metrics.json").is_file() \
        else newest(root, "metrics.json", t0, exclude=out)
    if not check(mfile is not None, "SESSION wrote metrics.json",
                 "no metrics.json found — write it into the --out directory"):
        return None
    try:
        metrics = json.loads(mfile.read_text())
    except json.JSONDecodeError as e:
        check(False, "metrics.json parses", str(e))
        return None
    check(True, "metrics.json parses")
    missing = [k for k in REQUIRED_KEYS if k not in metrics]
    check(not missing, "metrics has required keys", f"missing: {', '.join(missing)}")
    check(metrics.get("completed") is True, "session completed",
          f"completed = {metrics.get('completed')!r}")
    frames_dir = mfile.parent
    imgs = [p for p in frames_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTS]
    check(bool(imgs), "SESSION wrote frames", f"no images under {frames_dir}")
    metrics["_dir"] = str(frames_dir)
    metrics["_imgs"] = [str(p) for p in imgs]
    return metrics


def gameplay_keys(m: dict) -> dict:
    return {k: v for k, v in m.items() if k not in VOLATILE and not k.startswith("_")}


def ensure_allow(root: Path, rules: list[str]) -> str | None:
    """Merge Bash allow-rules into the project's .claude/settings.local.json."""
    sfile = root / ".claude" / "settings.local.json"
    try:
        settings = json.loads(sfile.read_text()) if sfile.is_file() else {}
    except json.JSONDecodeError:
        print(f"  !  {sfile} exists but is not valid JSON — add these rules by hand:")
        for r in rules:
            print(f"       {r}")
        return None
    allow = settings.setdefault("permissions", {}).setdefault("allow", [])
    added = [r for r in rules if r not in allow]
    if not added:
        return None
    allow.extend(added)
    sfile.parent.mkdir(parents=True, exist_ok=True)
    sfile.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n")
    return str(sfile)


def allow_rule(cmd: str) -> str:
    """A prefix permission rule from a frozen command: program + first non-flag arg."""
    parts = cmd.strip().split()
    prefix = " ".join(parts[:2]) if len(parts) > 1 and not parts[1].startswith("-") else parts[0]
    return f"Bash({prefix}:*)"


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: preflight.py .gamemaker/<slug>", file=sys.stderr)
        return 2
    runp = Path(sys.argv[1])
    harness_file = runp / "HARNESS.md"
    harness = read(harness_file)
    if not harness:
        print(f"error: no HARNESS.md in {runp}", file=sys.stderr)
        return 2
    root = runp.resolve().parent.parent
    here = Path(__file__).resolve().parent

    print(f"preflight — {runp.name}  (project root: {root})\n")

    cmds = {name: field(harness, name) for name in COMMANDS}
    print("frozen commands:")
    for name in COMMANDS:
        c = cmds[name]
        bad = not c or PLACEHOLDER.search(c)
        check(not bad, f"{name} is written and placeholder-free", c or "empty")

    session = cmds["SESSION"]
    if not session or PLACEHOLDER.search(session):
        print("\nNOT PROVEN — write the SESSION command first. "
              "Start from scripts/templates/ (see references/harness.md).")
        return 1

    scratch = Path(tempfile.mkdtemp(prefix="gm-preflight-"))
    print("\nrun 1:")
    m1 = session_once(session, root, scratch / "run1")
    print("run 2 (same seed — determinism):")
    m2 = session_once(session, root, scratch / "run2")

    if m1 and m2:
        g1, g2 = gameplay_keys(m1), gameplay_keys(m2)
        diff = sorted(k for k in (g1.keys() | g2.keys()) if g1.get(k) != g2.get(k))
        check(not diff, "same seed → same gameplay metrics",
              f"these keys differ across identical runs: {', '.join(diff)}. "
              "Un-seeded randomness somewhere — route it through the seeded RNG "
              "(references/code.md rule 1)")

    shot_img = None
    shot = cmds["SCREENSHOT"]
    if shot and not PLACEHOLDER.search(shot):
        print("screenshot:")
        sdir = scratch / "shot"
        sdir.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        proc = run(rewrite_out(shot, sdir) or shot, root)
        check(proc.returncode == 0, "SCREENSHOT exits 0",
              (proc.stderr or proc.stdout).strip()[-300:])
        shot_img = next((p for p in sdir.rglob("*") if p.suffix.lower() in IMAGE_EXTS), None) \
            or newest(root, "*.png", t0, exclude=scratch)
        check(shot_img is not None, "SCREENSHOT wrote an image")

    pair_src = shot_img or (Path(m1["_imgs"][0]) if m1 and m1.get("_imgs") else None)
    if pair_src:
        print("blind pair:")
        abdir = scratch / "abtest"
        proc = run(f'python3 "{here / "ab.py"}" --round "{abdir}" '
                   f'--ref "{pair_src}" --cand "{pair_src}"', root)
        check(proc.returncode == 0 and (abdir / "ab" / "key.json").is_file(),
              "ab.py builds a pair from the capture",
              (proc.stderr or proc.stdout).strip()[-300:])

    print()
    if failures:
        print(f"NOT PROVEN — {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        print("\nFix these and re-run. An unattended round past an unproven harness is a guess;")
        print("a firing spent failing the same gate is the most expensive way to find this out.")
        return 1

    new_harness = re.sub(r"^CAPTURE PROVEN:.*$", "CAPTURE PROVEN: yes",
                         harness, count=1, flags=re.M)
    if new_harness != harness:
        harness_file.write_text(new_harness)
        print("PASS — wrote CAPTURE PROVEN: yes to HARNESS.md")
    else:
        print("PASS — but HARNESS.md has no 'CAPTURE PROVEN:' line to flip; add one.")

    rules = [allow_rule(c) for n, c in cmds.items() if c and not PLACEHOLDER.search(c)]
    rules += [f"Bash(python3 {here}/*:*)", "Bash(git add:*)", "Bash(git commit:*)"]
    written = ensure_allow(root, sorted(set(rules)))
    if written:
        print(f"allowlist updated: {written}")
    shutil.rmtree(scratch, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
