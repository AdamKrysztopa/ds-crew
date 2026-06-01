#!/usr/bin/env python3
"""Assert the shipped skill set is exactly the canonical 14 — no silent additions
or drops, and every directory name matches its frontmatter `name`.

This is the guard for "all 14 skills actually register": a skill that gets renamed,
deleted, or has its frontmatter `name` drift out of sync with its directory would
otherwise only surface as a stale-cache mystery at runtime. Stdlib only.

    python3 check_skill_registry.py            # check skills/ from repo root
"""
import glob, os, sys

# The canonical shipped skill set. Update deliberately when adding/removing a skill
# (and update README "The fourteen skills" + plugin manifests to match).
EXPECTED_SKILLS = {
    "data-profile", "ds-clarify", "ds-conduct", "ds-env-setup", "ds-memory",
    "ds-model", "ds-reconcile", "ds-search", "ds-spike", "ds-star",
    "ds-star-plus", "ds-verify", "ds-vote", "eda-narrative",
}


def _frontmatter_name(path):
    """Return the `name:` value from a SKILL.md frontmatter block, or None."""
    with open(path) as fh:
        lines = fh.read().splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        k, _, v = line.partition(":")
        if k.strip() == "name":
            return v.strip()
    return None


def registry_errors(skills_root="skills"):
    """Return a list of human-readable problems with the skill registry."""
    errs = []
    found = {}  # dir name -> SKILL.md path
    for sk in sorted(glob.glob(os.path.join(skills_root, "*", "SKILL.md"))):
        found[os.path.basename(os.path.dirname(sk))] = sk

    discovered = set(found)
    for missing in sorted(EXPECTED_SKILLS - discovered):
        errs.append(f"expected skill missing from disk: {missing}/SKILL.md")
    for unexpected in sorted(discovered - EXPECTED_SKILLS):
        errs.append(f"undeclared skill on disk (add to EXPECTED_SKILLS?): {unexpected}")

    for name, path in found.items():
        if name not in EXPECTED_SKILLS:
            continue
        fm_name = _frontmatter_name(path)
        if fm_name != name:
            errs.append(f"{path}: frontmatter name {fm_name!r} != directory {name!r}")
    return errs


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "skills"
    errs = registry_errors(root)
    for e in errs:
        print(f"[REGISTRY] {e}")
    print(f"skill registry: {len(EXPECTED_SKILLS)} expected — "
          + ("OK" if not errs else "FAIL"))
    sys.exit(1 if errs else 0)
