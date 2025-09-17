#!/usr/bin/env python3
"""
Bank Statement Parser Agent
Parses bank PDFs/CSVs into pandas DataFrames and validates against reference CSV.
Generates parser + test automatically.
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import traceback
import importlib

try:
    from groq import Groq
    GROQ_API_KEY = "gsk_your_actual_key_here"
    client = Groq(api_key=GROQ_API_KEY)
except Exception:
    client = None
    print("[WARN] Groq client not available, using default parser.")

PROJECT_ROOT = Path(__file__).parent.resolve()
PARSERS_DIR = PROJECT_ROOT / "custom_parsers"
DATA_DIR = PROJECT_ROOT / "data"

EXPECTED_COLUMNS = ["Date", "Description", "Debit Amt", "Credit Amt", "Balance"]

DEFAULT_TEMPLATE = """\
import pandas as pd
import pdfplumber
from pathlib import Path

def parse(file_path: str) -> pd.DataFrame:
    df = pd.DataFrame()
    file_path = Path(file_path)
    if file_path.suffix.lower() == '.csv':
        df = pd.read_csv(file_path)
    elif file_path.suffix.lower() == '.pdf':
        rows = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    if not table:
                        continue
                    header = table[0]
                    for row in table[1:]:
                        if row == header or all((cell is None or str(cell).strip() == '') for cell in row):
                            continue
                        rows.append(row)
        if rows:
            df = pd.DataFrame(rows, columns=header)

    numeric_cols = ["Debit Amt", "Credit Amt", "Balance"]
    for col in df.columns:
        if any(nc.lower() in col.lower() for nc in numeric_cols):
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(',', '', regex=True).str.strip(),
                errors='coerce'
            ).fillna(0)

    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].fillna('').astype(str).str.strip()
    return df
"""

class BankParserAgent:
    def __init__(self):
        self.max_attempts = 3
        PARSERS_DIR.mkdir(exist_ok=True)

    def write_parser(self, bank: str, use_llm=False) -> Path:
        parser_path = PARSERS_DIR / f"{bank}_parser.py"
        parser_code = DEFAULT_TEMPLATE

        # Always use default template (no Groq or LLM)
        with open(parser_path, "w", encoding="utf-8") as f:
            f.write(parser_code)
        print(f" Written parser -> {parser_path}")
        return parser_path

    def test_parser(self, bank: str):
        sys.path.insert(0, str(PROJECT_ROOT))
        parser_module = importlib.import_module(f"custom_parsers.{bank}_parser")

        parse_func = getattr(parser_module, "parse", None)
        if not parse_func:
            raise AttributeError("parse function not found in parser")

        csv_file = DATA_DIR / bank / "result.csv"
        pdf_file = DATA_DIR / bank / "sample.pdf"
        file_to_parse = csv_file if csv_file.exists() else pdf_file
        if not file_to_parse.exists():
            raise FileNotFoundError(f"No data file found for {bank}: {csv_file} or {pdf_file}")

        df_out = parse_func(str(file_to_parse))
        df_out.columns = [c.strip() for c in df_out.columns]

        print(f"\n📄 Parsed DataFrame ({len(df_out)} rows, {len(df_out.columns)} columns):")
        print(df_out.head(5))

        if csv_file.exists():
            df_ref = pd.read_csv(csv_file)
            df_ref.columns = [c.strip() for c in df_ref.columns]

            # Normalize numeric columns
            for col in ["Debit Amt", "Credit Amt", "Balance"]:
                df_out[col] = pd.to_numeric(df_out[col], errors='coerce').fillna(0).round(2)
                df_ref[col] = pd.to_numeric(df_ref[col], errors='coerce').fillna(0).round(2)

            # Clean string columns
            for col in ["Date", "Description"]:
                df_out[col] = df_out[col].astype(str).str.strip()
                df_ref[col] = df_ref[col].astype(str).str.strip()

            mismatches = []
            for col in EXPECTED_COLUMNS:
                try:
                    pd.testing.assert_series_equal(
                        df_out[col].reset_index(drop=True),
                        df_ref[col].reset_index(drop=True),
                        check_dtype=False
                    )
                    print(f" Column '{col}' matches")
                except AssertionError:
                    mismatches.append(col)
                    print(f"❌ Column '{col}' does NOT match")

            if mismatches:
                raise AssertionError(f"Mismatched columns: {mismatches}")

        print("Parser test passed!\n")
        return True

    def run(self, bank: str):
        for attempt in range(1, self.max_attempts + 1):
            print(f"\n🔧 Attempt {attempt}/{self.max_attempts} for '{bank}'...")
            use_llm = False  # Always False, no LLM usage
            self.write_parser(bank, use_llm)
            try:
                self.test_parser(bank)
                print(f" Success on attempt {attempt}")
                return
            except Exception as e:
                print(f"❌ Attempt {attempt} failed: {e}")
                traceback.print_exc()
        print(f"🚨 All attempts failed for '{bank}'. Please check your data and parser.")

def main():
    parser = argparse.ArgumentParser(description="Bank Statement Parser Agent")
    parser.add_argument("--target", required=True, help="Bank target (e.g., icici)")
    args = parser.parse_args()

    agent = BankParserAgent()
    agent.run(args.target.strip().lower())

if __name__ == "__main__":
    main()
