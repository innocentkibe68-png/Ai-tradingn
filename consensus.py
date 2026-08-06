import logging
from collections import Counter
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

VALID_DIRECTIONS = {"BUY", "SELL", "NO TRADE"}


def build_consensus(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    valid_reviews = [
        review for review in reviews
        if review.get("direction") in VALID_DIRECTIONS
        and isinstance(review.get("confidence"), (int, float))
    ]

    if not valid_reviews:
        logging.error("No valid AI reviews returned. Defaulting to NO TRADE.")
        return {"direction": "NO TRADE", "confidence": 0, "agreement": 0.0,
                "reason": "No valid AI reviews were returned.",
                "risk_flags": ["NO_VALID_AI_REVIEWS"], "votes": {},
                "technical_summaries": "N/A"}

    votes_summary = [f"{r.get('provider', '?')}: {r['direction']} ({r['confidence']})" for r in valid_reviews]
    logging.info(f"AI votes: {', '.join(votes_summary)}")

    directions = [review["direction"] for review in valid_reviews]
    counts = Counter(directions)
    majority_direction, majority_count = counts.most_common(1)[0]
    agreement = majority_count / len(valid_reviews)
    average_confidence = sum(float(r["confidence"]) for r in valid_reviews) / len(valid_reviews)

    reasons = [r.get("reason", "") for r in valid_reviews if r.get("reason")]
    summaries = [r.get("technical_summary", "") for r in valid_reviews if r.get("technical_summary") and r.get("technical_summary") != "N/A"]
    risk_flags = list(set(flag for r in valid_reviews for flag in r.get("risk_flags", [])))

    if majority_direction != "NO TRADE" and agreement < 2 / 3:
        final_direction = "NO TRADE"
        risk_flags.append("INSUFFICIENT_AI_AGREEMENT")
        logging.warning(f"Majority {majority_direction} at {agreement:.0%} agreement. Downgraded to NO TRADE.")
    else:
        final_direction = majority_direction
        logging.info(f"Consensus: {final_direction} (agreement {agreement:.0%}).")

    return {
        "direction": final_direction,
        "confidence": round(average_confidence, 1),
        "agreement": round(agreement, 2),
        "reason": " | ".join(reasons),
        "technical_summaries": " | ".join(summaries) if summaries else "N/A",
        "risk_flags": risk_flags,
        "votes": dict(counts),
    }