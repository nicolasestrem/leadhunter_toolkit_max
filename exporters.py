import os, csv, json, datetime
from typing import List, Dict

OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT_DIR, exist_ok=True)

def export_csv(rows: list[dict]) -> str:
    if not rows:
        raise ValueError("No rows to export")
    fn = os.path.join(OUT_DIR, f"leads_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv")
    headers = sorted({k for r in rows for k in r.keys()})
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v) for k, v in r.items()})
    return fn

def export_json(rows: list[dict]) -> str:
    fn = os.path.join(OUT_DIR, f"leads_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    return fn
