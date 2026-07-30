from collections import Counter
from typing import List, Dict


VALID_DIRECTIONS = {"BUY", "SELL", "NO TRADE"}


def build_consensus(reviews: List[Dict]) -> Dict:
    valid_reviews = [
        review
        for review in reviews
        if review.get("direction") in VALID_DIRECTIONS
        and isinstance(review.get("confidence"), (int, float))
    ]

    if not valid_reviews:
        return {
            "direction": "NO TRADE",
            "confidence": 0.0,
            "agreement": 0.0,
            "reason": "No valid AI reviews were returned.",
            "risk_flags": ["NO_VALID_AI_REVIEWS"],
        }

    directions = [review["direction"] for review in valid_reviews]
    counts = Counter(directions)

    majority_direction, majority_count = counts.most_common(1)[0]

    agreement = majority_count / len(valid_reviews)

    average_confidence = sum(
        float(review["confidence"])
        for review in valid_reviews
    ) / len(valid_reviews)

    reasons = [
        review.get("reason", "")
        for review in valid_reviews
        if review.get("reason")
    ]

    risk_flags = []

    for review in valid_reviews:
        for flag in review.get("risk_flags", []):
            if flag not in risk_flags:
                risk_flags.append(flag)

    # Require at least 2/3 agreement before accepting BUY or SELL.
    if majority_direction != "NO TRADE" and agreement < 2 / 3:
        final_direction = "NO TRADE"
        risk_flags.append("INSUFFICIENT_AI_AGREEMENT")
    else:
        final_direction = majority_direction

    return {
        "direction": final_direction,
        "confidence": round(average_confidence, 3),
        "agreement": round(agreement, 3),
        "reason": " | ".join(reasons),
        "risk_flags": risk_flags,
        "votes": dict(counts),
    }