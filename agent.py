#!/usr/bin/env python3
import sys, argparse, importlib, traceback
from pathlib import Path
import pandas as pd, pdfplumber

ROOT, PARSERS, DATA = Path(_file_).parent.resolve(), Path("custom_parsers"), Path("data")
COLS = ["Date", "Description", "Debit Amt", "Credit Amt", "Balance"]
TEMPLATE = """\
import pandas as pd, pdfplumber
from pathlib import Path
def parse(p):
    p = Path(p)
    if p.suffix.lower() == ".csv": df = pd.read_csv(p)
    else:
        rows, hdr = [], []
        with pdfplumber.open(p) as pdf:
            for pg in pdf.pages:
                for t in pg.extract_tables() or []:
                    if t: hdr = t[0]; rows += [r for r in t[1:] if any(r)]
        df = pd.DataFrame(rows, columns=hdr) if rows else pd.DataFrame()
    for c in ["Debit Amt","Credit Amt","Balance"]:
        if c in df: df[c] = pd.to_numeric(df[c].astype(str).str.replace(',','',regex=True),errors='coerce').fillna(0)
    for c in df.select_dtypes('object'): df[c] = df[c].fillna('').astype(str).str.strip()
    return df
"""

class Agent:
    def run(self, bank):
        PARSERS.mkdir(exist_ok=True)
        parser_path = PARSERS / f"{bank}_parser.py"
        parser_path.write_text(TEMPLATE, encoding="utf-8")
        print(f"Parser written -> {parser_path}")
        try: self.test(bank)
        except Exception as e: print(f" Test failed: {e}"); traceback.print_exc()

    def test(self, bank):
        sys.path.insert(0, str(ROOT))
        parse = importlib.import_module(f"custom_parsers.{bank}_parser").parse
        csvf, pdff = DATA/bank/"result.csv", DATA/bank/"sample.pdf"
        f = csvf if csvf.exists() else pdff
        if not f.exists(): return print(f" No data found for {bank}. Place CSV or PDF in data/{bank}/")
        df_out = parse(f); df_out.columns = [c.strip() for c in df_out.columns]
        print(f"\n Parsed DataFrame ({len(df_out)} rows):\n", df_out.head())
        if csvf.exists():
            df_ref = pd.read_csv(csvf); df_ref.columns = [c.strip() for c in df_ref.columns]
            for c in ["Debit Amt","Credit Amt","Balance"]:
                for d in (df_out, df_ref): d[c] = pd.to_numeric(d[c], errors='coerce').fillna(0).round(2)
            for c in ["Date","Description"]:
                for d in (df_out, df_ref): d[c] = d[c].astype(str).str.strip()
            matched, mismatched = [], []
            for c in COLS:
                (matched if df_out[c].equals(df_ref[c]) else mismatched).append(c)
                print(f"{'' if df_out[c].equals(df_ref[c]) else ''} Column '{c}' {'matches' if df_out[c].equals(df_ref[c]) else 'does NOT match'}")
            print(f"\nMatched Columns: {matched}\nMismatched Columns: {mismatched}")

if _name_ == "_main_":
    p = argparse.ArgumentParser(); p.add_argument("--target", required=True)
    Agent().run(p.parse_args().target.lower())
