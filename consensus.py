import logging
from collections import Counter
from typing import List, Dict, Any

# Configure logging to match the rest of the pipeline
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

VALID_DIRECTIONS = {"BUY", "SELL", "NO TRADE"}


def build_consensus(reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates AI model reviews into a single, risk-managed consensus.
    Requires >= 66.7% agreement for any directional trade (BUY/SELL).
    """
    
    # 1. Filter out malformed or errored reviews
    valid_reviews = [
        review for review in reviews
        if review.get("direction") in VALID_DIRECTIONS
        and isinstance(review.get("confidence"), (int, float))
    ]

    if not valid_reviews:
        logging.error("No valid AI reviews returned. Defaulting to NO TRADE.")
        return {
            "direction": "NO TRADE",
            "confidence": 0,
            "agreement": 0.0,
            "reason": "No valid AI reviews were returned.",
            "risk_flags": ["NO_VALID_AI_REVIEWS"],
            "votes": {}
        }

    # 2. Log individual votes for pipeline observability
    votes_summary = [f"{r.get('provider', 'Unknown')}: {r['direction']} (Conf: {r['confidence']})" for r in valid_reviews]
    logging.info(f"AI Votes received: {', '.join(votes_summary)}")

    # 3. Calculate consensus metrics
    directions = [review["direction"] for review in valid_reviews]
    counts = Counter(directions)
    
    majority_direction, majority_count = counts.most_common(1)[0]
    agreement = majority_count / len(valid_reviews)
    
    # Calculate average confidence (0-100 scale)
    average_confidence = sum(float(review["confidence"]) for review in valid_reviews) / len(valid_reviews)

    # Aggregate unique reasons and risk flags
    reasons = [review.get("reason", "") for review in valid_reviews if review.get("reason")]
    risk_flags = list(set(flag for review in valid_reviews for flag in review.get("risk_flags", [])))

    # 4. Apply Institutional Risk Rule: Require >= 66.7% agreement for directional bias
    if majority_direction != "NO TRADE" and agreement < 2 / 3:
        final_direction = "NO TRADE"
        risk_flags.append("INSUFFICIENT_AI_AGREEMENT")
        logging.warning(f"Majority is {majority_direction} but agreement is only {agreement:.1%}. Downgraded to NO TRADE.")
    else:
        final_direction = majority_direction
        logging.info(f"Consensus reached: {final_direction} (Agreement: {agreement:.1%}, Avg Confidence: {average_confidence:.1f})")

    return {
        "direction": final_direction,
        "confidence": round(average_confidence, 1),
        "agreement": round(agreement, 2),
        "reason": " | ".join(reasons),
        "risk_flags": risk_flags,
        "votes": dict(counts),
    }