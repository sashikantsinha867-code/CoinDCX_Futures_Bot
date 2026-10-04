from decimal import Decimal, ROUND_DOWN


MIN_QUANTITY = Decimal("0.001")
QUANTITY_STEP = Decimal("0.001")

# Maximum capital risk per trade
RISK_PERCENT = Decimal("1.0")


def round_down_quantity(quantity):
    quantity = Decimal(str(quantity))

    quantity = (
        quantity / QUANTITY_STEP
    ).to_integral_value(
        rounding=ROUND_DOWN
    ) * QUANTITY_STEP

    return quantity


def calculate_position_size(
    available_inr,
    entry_price_usdt,
    stop_loss_price_usdt,
    leverage,
    usdt_inr_rate,
):
    """
    CoinDCX INR Futures position sizing.

    Final quantity is limited by BOTH:

    1. Risk-based quantity
       Risk = RISK_PERCENT of available INR

    2. Available-margin quantity
       Maximum notional = available INR * leverage

    Final quantity = smaller of the two.

    Quantity is rounded DOWN to the exchange quantity step.
    """

    available_inr = Decimal(str(available_inr))
    entry_price = Decimal(str(entry_price_usdt))
    stop_loss_price = Decimal(str(stop_loss_price_usdt))
    leverage = Decimal(str(leverage))
    usdt_inr_rate = Decimal(str(usdt_inr_rate))

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    if available_inr <= 0:
        return 0.0

    if entry_price <= 0:
        return 0.0

    if stop_loss_price <= 0:
        return 0.0

    if leverage <= 0:
        return 0.0

    if usdt_inr_rate <= 0:
        return 0.0

    # --------------------------------------------------
    # SL DISTANCE
    # --------------------------------------------------

    sl_distance_usdt = abs(
        entry_price - stop_loss_price
    )

    if sl_distance_usdt <= 0:
        return 0.0

    # --------------------------------------------------
    # 1% RISK
    # --------------------------------------------------

    risk_amount_inr = (
        available_inr
        * RISK_PERCENT
        / Decimal("100")
    )

    risk_amount_usdt = (
        risk_amount_inr
        / usdt_inr_rate
    )

    # Risk-based quantity
    risk_quantity = (
        risk_amount_usdt
        / sl_distance_usdt
    )

    # --------------------------------------------------
    # MAXIMUM AVAILABLE MARGIN
    # --------------------------------------------------

    # Available INR -> USDT
    available_usdt = (
        available_inr
        / usdt_inr_rate
    )

    # Maximum position notional allowed by leverage
    max_notional_usdt = (
        available_usdt
        * leverage
    )

    # Maximum quantity affordable
    margin_quantity = (
        max_notional_usdt
        / entry_price
    )

    # --------------------------------------------------
    # FINAL QUANTITY
    # --------------------------------------------------

    quantity = min(
        risk_quantity,
        margin_quantity
    )

    # --------------------------------------------------
    # ROUND DOWN
    # --------------------------------------------------

    quantity = round_down_quantity(
        quantity
    )

    # --------------------------------------------------
    # MINIMUM QUANTITY
    # --------------------------------------------------

    if quantity < MIN_QUANTITY:
        return 0.0

    return float(quantity)
