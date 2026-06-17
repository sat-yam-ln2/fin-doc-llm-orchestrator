from typing import Any


def extract_amount(value: str) -> float:
    if not value:
        return 0.0
    # Remove currency symbols and spaces
    cleaned = str(value).replace("$", "").replace(",", "").strip()
    # Take only the last number-like token (the actual amount)
    tokens = cleaned.split()
    for token in reversed(tokens):
        try:
            return float(token)
        except ValueError:
            continue
    return 0.0


def detect_anomalies(doc_type: str, extracted: Any) -> list:
    flags = []

    if doc_type == "bank_statement":
        credits = extract_amount(getattr(extracted, "total_credits", None))
        debits = extract_amount(getattr(extracted, "total_debits", None))
        transactions = getattr(extracted, "transactions", [])
        risk_keywords = [k.lower() for k in getattr(extracted, "risk_keywords", [])]

        # Rule 1: debits exceed credits by more than 3x
        if credits > 0 and debits > credits * 3:
            flags.append({
                "rule": "High Debit to Credit Ratio",
                "detail": f"Total debits (${debits:,.2f}) exceed total credits (${credits:,.2f}) by more than 3x",
                "severity": "high"
            })

        # Rule 2: single transaction exceeds 50% of total credits AND is above $5,000
        for txn in transactions:
            amount = extract_amount(txn)
            if credits > 0 and amount > credits * 0.5 and amount > 5000:
                flags.append({
                    "rule": "Large Single Transaction",
                    "detail": f"Transaction of ${amount:,.2f} exceeds 50% of total credits (${credits:,.2f})",
                    "severity": "medium"
                })

        # Rule 3: wire transfer present
        for txn in transactions:
            if "wire" in txn.lower() or "wire transfer" in txn.lower():
                flags.append({
                    "rule": "Wire Transfer Detected",
                    "detail": f"Wire transfer found: {txn.strip()}",
                    "severity": "medium"
                })

        # Rule 4: risk keywords in extracted fields
        high_risk_words = ["flagged", "suspicious", "international", "laundering"]
        for word in high_risk_words:
            if word in risk_keywords:
                flags.append({
                    "rule": "Risk Keyword Present",
                    "detail": f"High risk keyword detected: '{word}'",
                    "severity": "high"
                })

    elif doc_type == "invoice":
        amount = extract_amount(getattr(extracted, "amount", None))
        payment_terms = str(getattr(extracted, "line_items", "")).lower()

        if amount > 10000:
            flags.append({
                "rule": "High Value Invoice",
                "detail": f"Invoice amount ${amount:,.2f} exceeds $10,000 threshold",
                "severity": "medium"
            })

        if "wire transfer only" in payment_terms or "wire" in str(getattr(extracted, "amount", "")).lower():
            flags.append({
                "rule": "Wire Transfer Only Payment",
                "detail": "Invoice restricts payment to wire transfer only, reducing traceability",
                "severity": "high"
            })

    elif doc_type == "dispute_letter":
        amount = extract_amount(getattr(extracted, "disputed_amount", None))
        if amount > 1000:
            flags.append({
                "rule": "High Value Dispute",
                "detail": f"Disputed amount ${amount:,.2f} exceeds $1,000",
                "severity": "medium"
            })

    elif doc_type == "news_snippet":
        risk_keywords = [k.lower() for k in getattr(extracted, "risk_keywords", [])]
        critical = ["money laundering", "fraud", "investigation", "sanctions", "fincen"]
        for word in critical:
            if any(word in k for k in risk_keywords):
                flags.append({
                    "rule": "Critical Risk Keyword in News",
                    "detail": f"News contains high risk term: '{word}'",
                    "severity": "high"
                })

    return flags
