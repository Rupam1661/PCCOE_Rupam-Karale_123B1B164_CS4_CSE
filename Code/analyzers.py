"""Deterministic secure-coding checks. Detection stays rule-based; the LLM only explains."""
import os, re, glob

RULES = [
    ("SEC-01", r"\bgets\s*\(", "critical", "Use of gets()"),
    ("SEC-02", r"\b(strcpy|strcat|sprintf)\s*\(", "high", "Unbounded string function"),
    ("SEC-03", r'(password|passwd|secret|api_key)\w*\s*=\s*"[^"]+"', "high", "Hard-coded credential"),
    ("SEC-04", r"\bprintf\s*\(\s*[A-Za-z_]\w*\s*\)", "high", "Possible format-string vulnerability"),
    ("BND-01", r"\bmemcpy\s*\(", "medium", "memcpy length not clearly bounded"),
    ("MEM-01", r"=\s*(malloc|calloc)\s*\(", "medium", "Allocation result not checked for NULL"),
    ("RES-01", r"=\s*fopen\s*\(", "medium", "fopen result not checked for NULL"),
    ("STY-01", r"\bgoto\b", "low", "Use of goto"),
]
NULL_CHECK_RULES = {"MEM-01", "RES-01"}


def scan_text(fname, text):
    lines = text.splitlines()
    out = []
    for i, line in enumerate(lines):
        for rid, pat, sev, title in RULES:
            if not re.search(pat, line, re.IGNORECASE):
                continue
            if rid == "BND-01" and "sizeof" in line:
                continue
            if rid in NULL_CHECK_RULES and any("NULL" in l for l in lines[i + 1:i + 4]):
                continue
            out.append({"file": fname, "line": i + 1, "rule": rid, "severity": sev,
                        "title": title, "snippet": line.strip()})
    return out


def scan_folder(folder):
    res = []
    for p in sorted(glob.glob(os.path.join(folder, "**", "*.[ch]"), recursive=True)):
        txt = open(p, encoding="utf-8", errors="ignore").read()
        res += scan_text(os.path.relpath(p, folder), txt)
    return res
