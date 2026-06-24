import numpy as np


def calculate_zscores(values: list) -> dict:
    """
    Computes Z-score for each value in a list.
    Z-score = (value - mean) / standard_deviation
    
    Tells you how many standard deviations a value is from the average
    of the group. No LLM involved — pure statistics.
    
    Needs at least 2 values to compute meaningfully.
    With fewer than 3 values, std deviation is unreliable, so we
    still compute but flag it as low confidence.
    """
    if len(values) < 2:
        return {"scores": [0] * len(values), "mean": 0, "std": 0, "reliable": False}

    arr = np.array(values, dtype=float)
    mean = float(np.mean(arr))
    std = float(np.std(arr))

    if std == 0:
        # All values identical — no variation, no outliers possible
        return {
            "scores": [0.0] * len(values),
            "mean": mean,
            "std": 0,
            "reliable": len(values) >= 3
        }

    z_scores = [(v - mean) / std for v in arr]

    return {
        "scores": [round(z, 2) for z in z_scores],
        "mean": round(mean, 2),
        "std": round(std, 2),
        "reliable": len(values) >= 3
    }


def detect_temporal_anomalies(statements: list, threshold: float = 2.5) -> dict:
    """
    statements: list of dicts like
        [{"label": "Statement 1", "debits": 3100.0, "credits": 5200.0}, ...]
    
    Computes Z-scores on the debit values across all statements.
    Any statement with |Z-score| above the threshold is flagged
    as a temporal anomaly — unusual relative to the account's own history.
    
    threshold=2.5 is a standard statistical outlier cutoff
    (roughly 99% confidence under a normal distribution assumption).
    """
    debits = [s["debits"] for s in statements]
    z_result = calculate_zscores(debits)

    annotated = []
    flagged_months = []

    for i, stmt in enumerate(statements):
        z = z_result["scores"][i]
        is_outlier = abs(z) >= threshold

        annotated.append({
            **stmt,
            "z_score": z,
            "is_temporal_anomaly": is_outlier
        })

        if is_outlier:
            direction = "above" if z > 0 else "below"
            flagged_months.append({
                "label": stmt["label"],
                "z_score": z,
                "annotation": (
                    f"{stmt['label']} is {abs(z)} standard deviations "
                    f"{direction} the {len(statements)}-statement mean "
                    f"(${z_result['mean']:,.2f})."
                )
            })

    return {
        "statements": annotated,
        "mean_debits": z_result["mean"],
        "std_debits": z_result["std"],
        "reliable": z_result["reliable"],
        "flagged_months": flagged_months,
        "threshold_used": threshold
    }
