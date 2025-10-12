import os, json, datetime
import pandas as pd

OUT_DIR = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT_DIR, exist_ok=True)

def export_xlsx(rows: list[dict]) -> str:
    fn = os.path.join(OUT_DIR, f"leads_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx")
    if not rows:
        raise ValueError("No rows to export")
    df = pd.DataFrame(rows)
    df.to_excel(fn, index=False)
    return fn
