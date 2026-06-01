#!/usr/bin/env python3
"""Assert every references/ and scripts/ path named in a SKILL.md resolves on disk
(review item #8). Stdlib only; run from repo root or via CI.

    python3 check_skill_paths.py                 # check all skills/*/SKILL.md
    python3 check_skill_paths.py path/to/SKILL.md
"""
import glob, os, re, sys

# matches optional ../ hops and intermediate path segments, then references/<...>.<ext>
# or scripts/<...>.<ext>; examples:
#   references/rubric.md
#   ../ds-star-plus/references/model_routing.md
#   ../ds-star-plus/scripts/route_model.py
_PAT = re.compile(r"(?:(?:\.\./)+[\w.-]*/)?(?:references|scripts)/[\w./-]+\.(?:md|py|json|txt)")

def referenced_paths(text):
    seen, out = set(), []
    for m in _PAT.findall(text):
        if m not in seen:
            seen.add(m); out.append(m)
    return out

def unresolved_paths(skill_path):
    base = os.path.dirname(os.path.abspath(skill_path))
    text = open(skill_path).read()
    missing = []
    for rel in referenced_paths(text):
        if not os.path.exists(os.path.normpath(os.path.join(base, rel))):
            missing.append(rel)
    return missing

if __name__ == "__main__":
    paths = sys.argv[1:] or sorted(glob.glob("skills/*/SKILL.md"))
    failed = False
    for p in paths:
        for rel in unresolved_paths(p):
            print(f"[MISSING] {p}: {rel}")
            failed = True
    print("ALL RESOLVE" if not failed else "UNRESOLVED REFERENCES FOUND")
    sys.exit(1 if failed else 0)
