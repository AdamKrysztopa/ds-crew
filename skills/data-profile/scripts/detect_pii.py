#!/usr/bin/env python3
"""Heuristic PII/sensitive-column detection for data-profile (cross-cutting safety).

Flags columns whose NAME hints at PII or whose VALUES mostly match a PII pattern,
so sensitive data is surfaced before anything leaves the sandbox. Heuristic, not
a guarantee — stdlib only, no network, no model call.

    from detect_pii import scan_columns
    report = scan_columns({"email": [...], "age": [...]})   # -> {"email": {"email"}}
"""
import re

_PATTERNS = {
    "email": re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
    "ssn": re.compile(r"^\d{3}-\d{2}-\d{4}$"),
    "credit_card": re.compile(r"^(?:\d[ -]?){13,16}$"),
    "phone": re.compile(r"^\+?\d[\d\s().-]{7,}\d$"),
    "ip": re.compile(r"^\d{1,3}(\.\d{1,3}){3}$"),
}
_NAME_HINTS = {
    "email": ("email", "e-mail", "mail"),
    "ssn": ("ssn", "social_security"),
    "credit_card": ("card", "ccnum", "creditcard"),
    "phone": ("phone", "mobile", "tel"),
    "name": ("first_name", "last_name", "full_name", "fullname"),
    "address": ("address", "street", "zipcode", "postcode"),
    "dob": ("dob", "birth", "date_of_birth"),
}

def scan_value(value):
    s = str(value).strip()
    return {kind for kind, pat in _PATTERNS.items() if pat.match(s)}

def scan_column(name, values, sample=200, threshold=0.5):
    kinds = set()
    low = name.lower()
    for kind, hints in _NAME_HINTS.items():
        if any(h in low for h in hints):
            kinds.add(kind)
    vals = [v for v in list(values)[:sample] if str(v).strip() != ""]
    if vals:
        for kind in _PATTERNS:
            hits = sum(1 for v in vals if kind in scan_value(v))
            if hits / len(vals) >= threshold:
                kinds.add(kind)
    return kinds

def scan_columns(columns):
    report = {}
    for name, values in columns.items():
        kinds = scan_column(name, values)
        if kinds:
            report[name] = kinds
    return report

if __name__ == "__main__":
    print(scan_columns({"email": ["a@b.com", "c@d.com"], "age": [30, 40]}))
