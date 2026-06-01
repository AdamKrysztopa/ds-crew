#!/usr/bin/env python3
"""Audit the arXiv ids in papers/README.md (Phase 0 credibility).

Parses the re-fetch curl heredoc, then (optionally, online) fetches each
abstract page to confirm the id resolves. Pure parsing is unit-tested; the
network check runs only when called as a script with --online.

    python3 verify_citations.py ../papers/README.md            # parse + list ids
    python3 verify_citations.py ../papers/README.md --online   # also HTTP-check each id
"""
import re, sys

_LINE = re.compile(r"^(\S+\.pdf)\s+(\d{4}\.\d{4,5})\s*$")

def parse_ids_from_curl_block(text):
    out = []
    for line in text.splitlines():
        m = _LINE.match(line.strip())
        if m:
            out.append((m.group(1), m.group(2)))
    return out

def abs_url(arxiv_id):
    return f"https://arxiv.org/abs/{arxiv_id}"

def _check_online(arxiv_id):
    import urllib.request, urllib.error
    try:
        req = urllib.request.Request(abs_url(arxiv_id), headers={"User-Agent": "ds-crew-citation-audit"})
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read(20000).decode("utf-8", "replace")
        return ("<title>" in body and "arXiv" in body, body)
    except Exception as e:  # noqa: BLE001
        return (False, str(e))

if __name__ == "__main__":
    path = sys.argv[1]
    online = "--online" in sys.argv
    ids = parse_ids_from_curl_block(open(path).read())
    for fname, aid in ids:
        if online:
            ok, _ = _check_online(aid)
            print(f"{aid:14} {'OK ' if ok else 'FAIL'} {fname}")
        else:
            print(f"{aid:14} {fname}  -> {abs_url(aid)}")
