def calculate_risk(
    account_balance: float,
    entry: float,
    stop_loss: float,
    direction: str,
    risk_percent: float = 1.0,
    reward_risk: float = 2.0,
) -> dict:
    if account_balance <= 0:
        raise ValueError("Account balance must be greater than 0.")

    if entry <= 0 or stop_loss <= 0:
        raise ValueError("Entry and stop-loss must be greater than 0.")

    if direction not in {"BUY", "SELL"}:
        raise ValueError("Direction must be BUY or SELL.")

    risk_amount = account_balance * (risk_percent / 100)

    if direction == "BUY":
        stop_distance = entry - stop_loss

        if stop_distance <= 0:
            raise ValueError("For BUY, stop-loss must be below entry.")

        take_profit = entry + (stop_distance * reward_risk)

    else:
        stop_distance = stop_loss - entry

        if stop_distance <= 0:
            raise ValueError("For SELL, stop-loss must be above entry.")

        take_profit = entry - (stop_distance * reward_risk)

    return {
        "risk_percent": risk_percent,
        "risk_amount": risk_amount,
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "reward_risk": reward_risk,
        "stop_distance": stop_distance,
    }