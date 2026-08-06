import logging
from collections import Counter
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

VALID_DIRECTIONS = {"BUY", "SELL", "NO TRADE"}
FAILURE_FLAGS = {"API_FAILURE", "INVALID_MODEL_OUTPUT", "MISSING_API_KEY", "MISSING_MODEL_NAME", "EMPTY_EVIDENCE"}


def build_consensus(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Only a review that actually analyzed the data counts as a vote.
    valid_reviews = [
        r for r in reviews
        if r.get("direction") in VALID_DIRECTIONS
        and isinstance(r.get("confidence"), (int, float))
        and not FAILURE_FLAGS.intersection(r.get("risk_flags", []))
    ]

    failed = [r.get("provider", "?") for r in reviews if r not in valid_reviews]
    if failed:
        logging.warning(f"Analysts unavailable: {', '.join(failed)}")

    risk_flags = list(set(flag for r in reviews for flag in r.get("risk_flags", [])))
    online_note = f"[Analysts online: {len(valid_reviews)}/{len(reviews)}] " if failed else ""

    if len(valid_reviews) < 2:
        logging.error("Fewer than 2 working analysts. NO TRADE.")
        return {
            "direction": "NO TRADE",
            "confidence": 0,
            "agreement": 0.0,
            "reason": online_note + "Insufficient working analysts to form a consensus.",
            "technical_summaries": "N/A",
            "risk_flags": risk_flags + ["INSUFFICIENT_ANALYSTS"],
            "votes": {},
        }

    directions = [r["direction"] for r in valid_reviews]
    counts = Counter(directions)
    majority_direction, majority_count = counts.most_common(1)[0]
    agreement = majority_count / len(valid_reviews)
    average_confidence = sum(float(r["confidence"]) for r in valid_reviews) / len(valid_reviews)

    reasons = [r.get("reason", "") for r in valid_reviews if r.get("reason")]
    summaries = [r.get("technical_summary", "") for r in valid_reviews
                 if r.get("technical_summary") and r.get("technical_summary") != "N/A"]

    if majority_direction != "NO TRADE" and agreement < 2 / 3:
        final_direction = "NO TRADE"
        risk_flags.append("INSUFFICIENT_AI_AGREEMENT")
        logging.warning(f"Majority {majority_direction} at {agreement:.0%}. Downgraded to NO TRADE.")
    else:
        final_direction = majority_direction

    return {
        "direction": final_direction,
        "confidence": round(average_confidence, 1),
        "agreement": round(agreement, 2),
        "reason": online_note + " | ".join(reasons),
        "technical_summaries": " | ".join(summaries) if summaries else "N/A",
        "risk_flags": risk_flags,
        "votes": dict(counts),
    }