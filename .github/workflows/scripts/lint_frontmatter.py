#!/usr/bin/env python3
"""Lint every skills/*/SKILL.md for required YAML frontmatter (Phase 0 CI).

A valid SKILL.md starts with a `---` block containing at least `name` and a
non-empty `description`. Stdlib only (no PyYAML dependency).

    python3 lint_frontmatter.py            # lint skills/*/SKILL.md from repo root
    python3 lint_frontmatter.py path...    # lint specific files
"""
import glob, sys

def parse_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fm, i = {}, 1
    while i < len(lines) and lines[i].strip() != "---":
        if ":" in lines[i]:
            k, _, v = lines[i].partition(":")
            fm[k.strip()] = v.strip()
        i += 1
    return {} if i >= len(lines) else fm  # unterminated block -> invalid

def lint_skill(text):
    errs = []
    fm = parse_frontmatter(text)
    if not fm:
        errs.append("no frontmatter block (must start with --- ... ---)")
        return errs
    if not fm.get("name"):
        errs.append("missing 'name'")
    if not fm.get("description"):
        errs.append("missing 'description'")
    return errs

if __name__ == "__main__":
    paths = sys.argv[1:] or sorted(glob.glob("skills/*/SKILL.md"))
    failed = False
    for p in paths:
        errs = lint_skill(open(p).read())
        if errs:
            failed = True
            for e in errs:
                print(f"{p}: {e}")
    print("frontmatter lint: " + ("FAIL" if failed else "OK"))
    sys.exit(1 if failed else 0)
