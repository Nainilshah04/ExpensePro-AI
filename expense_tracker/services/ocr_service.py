import re
from datetime import datetime, date
from .ai_service import ai_engine

class OCRReceiptParser:
    """
    Intelligent Entity Extraction Engine for Receipt Text.
    Extracts Merchant name, Date, Currency Amount, and maps to Category.
    """

    KNOWN_MERCHANTS = [
        "starbucks", "mcdonalds", "dominos", "pizza hut", "subway", "kfc",
        "burger king", "reliance retail", "dmart", "d-mart", "spencer", "decathlon",
        "zara", "h&m", "ikea", "croma", "apple store", "apollo pharmacy",
        "shell", "hp petrol", "indian oil", "uber", "ola", "haldirams",
        "blinkit", "zepto", "swiggy", "zomato", "cult.fit", "tatasky", "airtel",
        "jio", "bescom", "mahadiscom", "torrent", "adani"
    ]

    # Priority patterns: Explicitly labeled dates like "Bill Date", "Invoice Date", "Date:"
    LABELED_DATE_PATTERNS = [
        r'(?:invoice\s*date|bill\s*date|date\s*of\s*issue|txn\s*date|trans\s*date|billing\s*date|dated?)\s*[:\-\s]\s*([0-9]{1,2}[/\.\-][0-9]{1,2}[/\.\-][0-9]{2,4})',
        r'(?:invoice\s*date|bill\s*date|date\s*of\s*issue|txn\s*date|trans\s*date|billing\s*date|dated?)\s*[:\-\s]\s*([0-9]{1,2}\s+[A-Za-z]{3,9}\s+[0-9]{2,4})',
        r'(?:invoice\s*date|bill\s*date|date\s*of\s*issue|txn\s*date|trans\s*date|billing\s*date|dated?)\s*[:\-\s]\s*([A-Za-z]{3,9}\s+[0-9]{1,2},?\s+[0-9]{2,4})'
    ]

    # General fallback date patterns
    FALLBACK_DATE_PATTERNS = [
        r'(\b\d{1,2}[/\.\-]\d{1,2}[/\.\-]\d{2,4}\b)',          # 15/08/2026 or 15.08.2026 or 15-08-2026
        r'(\b\d{4}[/\.\-]\d{1,2}[/\.\-]\d{1,2}\b)',          # 2026-08-15
        r'(\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b)', # 15 Aug 2026
        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b)'   # Aug 15, 2026
    ]

    TOTAL_PATTERNS = [
        r'(?:total|grand\s*total|net\s*amount|amount\s*payable|amount\s*due|final\s*amount|bill\s*amount|balance\s*due|subtotal)[\s:]*(?:rs\.?|inr|₹|\$)?\s*([\d,]+\.?\d*)',
        r'(?:rs\.?|inr|₹|\$)\s*([\d,]+\.\d{2})',
        r'([\d,]+\.\d{2})\s*(?:total|paid|cash|card|upi)'
    ]

    LEGAL_OR_HEADER_TERMS = r'\b(tax|invoice|receipt|welcome|bill|cashier|gstin|cin|tel|phone|store\s*#|jurisdiction|subject\s*to|terms|conditions|thank\s*you|customer\s*copy|retail\s*invoice|original\s*for\s*recipient|mumbai|thane|delhi|bangalore)\b'

    def parse_text(self, text: str):
        if not text or not text.strip():
            return {
                "success": False,
                "error": "Empty OCR text received"
            }

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # 1. Extract Merchant Name
        merchant = self._extract_merchant(lines)

        # 2. Extract Date (Contextual / Bill Date prioritized)
        tx_date = self._extract_date(text)

        # 3. Extract Amount
        amount = self._extract_amount(text, lines)

        # 4. Predict Category
        query_text = f"{merchant} {' '.join(lines[:6])}"
        category_pred = ai_engine.predict_category(query_text)

        return {
            "success": True,
            "merchant": merchant,
            "date": tx_date.strftime("%Y-%m-%d") if tx_date else date.today().strftime("%Y-%m-%d"),
            "amount": amount,
            "category": category_pred.get("category", "Other"),
            "confidence": category_pred.get("confidence", 0.7),
            "raw_preview": "\n".join(lines[:10])
        }

    def _extract_merchant(self, lines):
        full_blob = " ".join(lines[:10]).lower()
        
        # 1. Look for recognized brands first
        for km in self.KNOWN_MERCHANTS:
            if km in full_blob:
                return km.title()

        # 2. Scan top 5 lines, filtering out legal clauses, GST numbers, and boilerplate
        for line in lines[:5]:
            clean = re.sub(r'[^a-zA-Z0-9\s&]', '', line).strip()
            if len(clean) > 3:
                # If line contains legal words like "Jurisdiction" or "Subject to", skip!
                if re.search(self.LEGAL_OR_HEADER_TERMS, clean, re.IGNORECASE):
                    continue
                return clean.title()

        return "Retail Store / Merchant"

    def _extract_date(self, text):
        # Step 1: Look for explicitly labeled dates (Invoice Date, Bill Date, Date)
        for pattern in self.LABELED_DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_candidate = self._parse_date_string(match.group(1))
                if date_candidate:
                    return date_candidate

        # Step 2: Fallback to general date regexes
        for pattern in self.FALLBACK_DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_candidate = self._parse_date_string(match.group(1))
                if date_candidate:
                    return date_candidate

        return None

    def _parse_date_string(self, date_str):
        clean_str = date_str.replace('/', '-').replace('.', '-').strip()
        # Prefer DD-MM-YYYY formats standard in Indian receipts
        formats = (
            "%d-%m-%Y", "%d-%m-%y",
            "%d-%b-%Y", "%d-%b-%y", "%d %b %Y", "%d %b %y",
            "%d-%B-%Y", "%d %B %Y",
            "%Y-%m-%d",
            "%m-%d-%Y", "%m-%d-%y",
            "%b %d, %Y", "%B %d, %Y"
        )
        for fmt in formats:
            try:
                dt = datetime.strptime(clean_str, fmt).date()
                # Sanity check: date within reasonable bounds (2015 to 2030)
                if 2015 <= dt.year <= 2030:
                    return dt
            except ValueError:
                continue
        return None

    def _extract_amount(self, text, lines):
        amounts = []
        for pattern in self.TOTAL_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                val_str = m.group(1).replace(',', '')
                try:
                    val = float(val_str)
                    if 0.5 < val < 2000000:
                        amounts.append(val)
                except ValueError:
                    pass

        if amounts:
            return max(amounts)

        # Fallback: check bottom lines for decimal currency values
        bottom_lines = lines[-6:] if len(lines) >= 6 else lines
        for line in reversed(bottom_lines):
            num_matches = re.findall(r'\b(\d+\.\d{2})\b', line)
            if num_matches:
                try:
                    return float(num_matches[-1])
                except ValueError:
                    pass

        return 0.0

ocr_parser = OCRReceiptParser()
