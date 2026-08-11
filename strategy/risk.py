def calculate_position_size(
    capital,
    risk_percent,
    entry_price,
    stop_loss_price,
    leverage=5
):
    """
    Calculate position size using:
    1. Risk-based quantity
    2. Maximum capital x leverage notional cap

    Returns BTC quantity.
    """

    capital = float(capital)
    risk_percent = float(risk_percent)
    entry_price = float(entry_price)
    stop_loss_price = float(stop_loss_price)
    leverage = float(leverage)

    if capital <= 0 or entry_price <= 0 or leverage <= 0:
        return 0.0

    risk_amount = capital * (risk_percent / 100)

    stop_loss_distance = abs(entry_price - stop_loss_price)

    if stop_loss_distance <= 0:
        return 0.0

    # Risk-based quantity
    risk_quantity = risk_amount / stop_loss_distance

    # Maximum notional allowed by capital and leverage
    max_notional = capital * leverage

    # Maximum quantity allowed by capital
    max_quantity = max_notional / entry_price

    quantity = min(risk_quantity, max_quantity)

    # CoinDCX BTC quantity increment = 0.001
    quantity = int(quantity * 1000) / 1000

    return round(quantity, 3)
