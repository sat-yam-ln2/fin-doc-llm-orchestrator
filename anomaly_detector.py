import re
import numpy as np
from typing import Any
from sklearn.ensemble import IsolationForest


def extract_amount(value: str) -> float:
    if not value:
        return 0.0
    cleaned = str(value).replace("$", "").replace(",", "").strip()
    tokens = cleaned.split()
    for token in reversed(tokens):
        try:
            return float(token)
        except ValueError:
            continue
    return 0.0


def run_isolation_forest(amounts: list) -> dict:
    """
    Takes a list of transaction amounts.
    Returns a dict mapping each amount to its anomaly score and label.

    Score closer to 1.0 = more anomalous.
    Score closer to 0.0 = more normal.
    Label -1 = anomaly. Label 1 = normal.

    Needs at least 3 transactions to run meaningfully.
    Falls back to empty dict if not enough data.
    """
    if len(amounts) < 3:
        return {}

    # Reshape to 2D array as scikit-learn expects (n_samples, n_features)
    X = np.array(amounts).reshape(-1, 1)

    # contamination = expected proportion of anomalies in the data
    # 'auto' lets the algorithm decide based on the data distribution
    # You can set this to 0.1 (10%) if you want stricter flagging
    clf = IsolationForest(contamination="auto", random_state=42)
    clf.fit(X)

    # decision_function returns raw anomaly scores
    # More negative = more anomalous
    # We flip and normalize to 0-1 scale so higher = more anomalous
    raw_scores = clf.decision_function(X)
    normalized = 1 - (raw_scores - raw_scores.min()) / (
        raw_scores.max() - raw_scores.min() + 1e-9
    )

    labels = clf.predict(X)  # -1 = anomaly, 1 = normal

    results = {}
    for i, amount in enumerate(amounts):
        results[amount] = {
            "anomaly_score": round(float(normalized[i]), 3),
            "is_anomaly": labels[i] == -1
        }
    return results


def detect_anomalies(doc_type: str, extracted: Any) -> list:
    flags = []

    if doc_type == "bank_statement":
        credits = extract_amount(getattr(extracted, "total_credits", None))
        debits = extract_amount(getattr(extracted, "total_debits", None))
        transactions = getattr(extracted, "transactions", [])
        risk_keywords = [k.lower() for k in getattr(extracted, "risk_keywords", [])]

        # ── Rule 1: High debit to credit ratio (keep this rule, it is account-level) ──
        if credits > 0 and debits > credits * 3:
            flags.append({
                "rule": "High Debit to Credit Ratio",
                "detail": f"Total debits (${debits:,.2f}) exceed total credits (${credits:,.2f}) by more than 3x",
                "severity": "high",
                "source": "rule"
            })

        # ── Rule 2: Wire transfer present (keep, it is keyword-based) ──
        for txn in transactions:
            if "wire" in txn.lower():
                flags.append({
                    "rule": "Wire Transfer Detected",
                    "detail": f"Wire transfer found: {txn.strip()}",
                    "severity": "medium",
                    "source": "rule"
                })

        # ── Rule 3: Risk keywords ──
        high_risk_words = ["flagged", "suspicious", "international", "laundering"]
        for word in high_risk_words:
            if word in risk_keywords:
                flags.append({
                    "rule": "Risk Keyword Present",
                    "detail": f"High risk keyword detected: '{word}'",
                    "severity": "high",
                    "source": "rule"
                })

        # ── Isolation Forest: replaces all hardcoded amount thresholds ──
        amounts = [extract_amount(txn) for txn in transactions]
        amounts = [a for a in amounts if a > 0]  # remove zeros and unparseable

        if amounts:
            if_results = run_isolation_forest(amounts)

            for txn, amount in zip(transactions, amounts):
                result = if_results.get(amount)
                if result and result["is_anomaly"]:
                    score = result["anomaly_score"]
                    severity = "high" if score >= 0.75 else "medium"
                    flags.append({
                        "rule": "Isolation Forest: Statistical Outlier",
                        "detail": (
                            f"Transaction '{txn.strip()}' amount ${amount:,.2f} "
                            f"is statistically anomalous (score: {score:.2f}). "
                            f"Model flagged this without any hardcoded threshold."
                        ),
                        "severity": severity,
                        "source": "isolation_forest",
                        "anomaly_score": score,
                        "amount": amount,
                        "transaction": txn.strip()
                    })

    elif doc_type == "invoice":
        amount = extract_amount(getattr(extracted, "amount", None))
        line_items_raw = str(getattr(extracted, "line_items", "")).lower()

        if amount > 10000:
            flags.append({
                "rule": "High Value Invoice",
                "detail": f"Invoice amount ${amount:,.2f} exceeds $10,000 threshold",
                "severity": "medium",
                "source": "rule"
            })

        if "wire transfer only" in line_items_raw or "wire" in line_items_raw:
            flags.append({
                "rule": "Wire Transfer Only Payment",
                "detail": "Invoice restricts payment to wire transfer only",
                "severity": "high",
                "source": "rule"
            })

    elif doc_type == "dispute_letter":
        amount = extract_amount(getattr(extracted, "disputed_amount", None))
        if amount > 1000:
            flags.append({
                "rule": "High Value Dispute",
                "detail": f"Disputed amount ${amount:,.2f} exceeds $1,000",
                "severity": "medium",
                "source": "rule"
            })

    elif doc_type == "news_snippet":
        risk_keywords = [k.lower() for k in getattr(extracted, "risk_keywords", [])]
        critical = ["money laundering", "fraud", "investigation", "sanctions", "fincen"]
        for word in critical:
            if any(word in k for k in risk_keywords):
                flags.append({
                    "rule": "Critical Risk Keyword in News",
                    "detail": f"News contains high risk term: '{word}'",
                    "severity": "high",
                    "source": "rule"
                })

    return flags
