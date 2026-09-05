import io
import pandas as pd
from datetime import datetime, date
from .ai_service import ai_engine

class BankCSVParser:
    """
    Parses and ingests bank statements and expense CSV exports (HDFC, SBI, ICICI, etc.).
    Automatically normalizes date, amount, description, and runs AI auto-categorization.
    """

    DATE_COLS = ["date", "txn date", "transaction date", "value date", "trans date"]
    DESC_COLS = ["narration", "description", "particulars", "remarks", "details", "note", "payee"]
    AMOUNT_COLS = ["debit", "withdrawal", "withdrawal amt.", "debit amount", "amount", "spent", "dr"]
    CATEGORY_COLS = ["category", "type", "tag"]

    def parse_csv(self, file_storage):
        try:
            # Read into dataframe with flexible encoding
            content = file_storage.read()
            try:
                df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(content), encoding='latin1')

            if df.empty:
                return {"success": False, "error": "CSV file is empty."}

            # Normalize column names
            col_map = {c: str(c).strip().lower() for c in df.columns}
            df.rename(columns=col_map, inplace=True)

            # Identify critical columns
            date_col = next((c for c in df.columns if any(k in c for k in self.DATE_COLS)), None)
            desc_col = next((c for c in df.columns if any(k in c for k in self.DESC_COLS)), None)
            amt_col = next((c for c in df.columns if any(k in c for k in self.AMOUNT_COLS)), None)
            cat_col = next((c for c in df.columns if any(k in c for k in self.CATEGORY_COLS)), None)

            if not amt_col:
                return {"success": False, "error": "Could not identify an Amount / Debit column in the CSV."}

            parsed_records = []
            for _, row in df.iterrows():
                # Process amount
                raw_amt = str(row[amt_col]).replace(',', '').strip()
                if not raw_amt or raw_amt.lower() in ('nan', 'none', '-'):
                    continue
                try:
                    amount = abs(float(raw_amt))
                    if amount <= 0:
                        continue
                except ValueError:
                    continue

                # Process description
                desc = str(row[desc_col]).strip() if desc_col and pd.notna(row[desc_col]) else "Bank Transaction"

                # Process date
                tx_date = date.today()
                if date_col and pd.notna(row[date_col]):
                    raw_date = str(row[date_col]).strip()
                    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d-%b-%Y", "%m/%d/%Y", "%d/%m/%y"):
                        try:
                            tx_date = datetime.strptime(raw_date.split()[0], fmt).date()
                            break
                        except ValueError:
                            continue

                # Process or predict category
                if cat_col and pd.notna(row[cat_col]) and str(row[cat_col]).strip():
                    cat = str(row[cat_col]).strip().title()
                else:
                    pred = ai_engine.predict_category(desc)
                    cat = pred.get("category", "Other")

                parsed_records.append({
                    "date": tx_date,
                    "amount": round(amount, 2),
                    "note": desc[:150],
                    "category": cat
                })

            return {
                "success": True,
                "count": len(parsed_records),
                "records": parsed_records
            }

        except Exception as e:
            return {"success": False, "error": f"Error parsing CSV: {str(e)}"}

csv_parser = BankCSVParser()
