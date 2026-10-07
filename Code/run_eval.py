"""Evaluation: scanner precision/recall vs seeded-bug markers + retrieval hit-rate. Run: python run_eval.py"""
import os, re, glob, csv, json, time
import config
from analyzers import scan_folder


def ground_truth():
    gt = set()
    for p in glob.glob(os.path.join(config.CODE_DIR, "**", "*.[ch]"), recursive=True):
        name = os.path.relpath(p, config.CODE_DIR)
        for i, line in enumerate(open(p, encoding="utf-8").read().splitlines(), 1):
            m = re.search(r"BUG:([A-Z]+-\d+)", line)
            if m:
                gt.add((name, i, m.group(1)))
    return gt


def eval_scanner():
    gt = ground_truth()
    pred = {(f["file"], f["line"], f["rule"]) for f in scan_folder(config.CODE_DIR)}
    tp, fp, fn = len(gt & pred), len(pred - gt), len(gt - pred)
    prec = tp / (tp + fp) if tp + fp else 0
    rec = tp / (tp + fn) if tp + fn else 0
    return {"seeded_bugs": len(gt), "detected": len(pred), "TP": tp, "FP": fp, "FN": fn,
            "precision": round(prec, 3), "recall": round(rec, 3)}


QUESTIONS = [
    ("Which function copies a name using strcpy?", "set_name"),
    ("Where is the hard-coded password stored?", "diag_password"),
    ("Which function reads input with gets and can overflow?", "read_input"),
    ("Where is goto used for error handling?", "retry"),
    ("Which function opens the config file with fopen?", "read_config"),
]


def eval_retrieval():
    from rag import VectorIndex, load_code_chunks
    idx = VectorIndex(load_code_chunks(config.CODE_DIR))
    rows = []
    for q, kw in QUESTIONS:
        t = time.time()
        hits = idx.search(q, config.TOP_K)
        ok = any(kw in h["text"] for h in hits)
        rows.append({"question": q, "expected_keyword": kw, "hit_in_top3": ok,
                     "cited": "; ".join(f"{h['file']}:{h['start']}-{h['end']}" for h in hits),
                     "latency_s": round(time.time() - t, 3)})
    return rows


if __name__ == "__main__":
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    s = eval_scanner()
    print("SCANNER:", s)
    r = eval_retrieval()
    for x in r:
        print(x)
    rate = sum(x["hit_in_top3"] for x in r) / len(r)
    print("RETRIEVAL HIT RATE:", rate)
    with open(os.path.join(config.RESULTS_DIR, "retrieval_eval.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=r[0].keys()); w.writeheader(); w.writerows(r)
    json.dump({"scanner": s, "retrieval_hit_rate": rate}, open(os.path.join(config.RESULTS_DIR, "eval_summary.json"), "w"), indent=2)
