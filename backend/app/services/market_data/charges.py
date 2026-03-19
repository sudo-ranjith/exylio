"""
Exylio Charge Calculator
Computes exact Angel One delivery charges per trade
and net P&L after all fees.
"""


def calculate_delivery_charges(buy_value: float, sell_value: float) -> dict:
    """
    Calculate all charges for a delivery (CNC) round trip.
    Returns itemised breakdown + totals.
    """
    turnover = buy_value + sell_value

    brokerage_buy  = min(buy_value  * 0.001, 20)   # 0.1% or ₹20 max
    brokerage_sell = min(sell_value * 0.001, 20)
    brokerage      = brokerage_buy + brokerage_sell

    stt_buy    = buy_value  * 0.001                  # 0.1% on buy
    stt_sell   = sell_value * 0.001                  # 0.1% on sell
    stt        = stt_buy + stt_sell

    nse_txn    = turnover   * 0.0000307              # 0.00307%
    stamp_duty = buy_value  * 0.00015                # 0.015% on buy only
    sebi_fee   = turnover   * 0.000001               # 0.0001%
    dp_charge  = 20.0                                # flat ₹20 per scrip per sell

    gst_base   = brokerage + nse_txn + sebi_fee
    gst        = gst_base * 0.18

    total = brokerage + stt + nse_txn + stamp_duty + sebi_fee + dp_charge + gst

    return {
        "brokerage":    round(brokerage, 2),
        "stt":          round(stt, 2),
        "nse_txn":      round(nse_txn, 2),
        "stamp_duty":   round(stamp_duty, 2),
        "sebi_fee":     round(sebi_fee, 4),
        "dp_charge":    round(dp_charge, 2),
        "gst":          round(gst, 2),
        "total_charges": round(total, 2),
    }


def calculate_net_pnl(buy_price: float, sell_price: float, quantity: int) -> dict:
    """
    Given entry/exit prices and qty, return full P&L summary
    including gross, charges, and net in-hand amount.
    """
    buy_value    = buy_price  * quantity
    sell_value   = sell_price * quantity
    gross_pnl    = sell_value - buy_value
    charges      = calculate_delivery_charges(buy_value, sell_value)
    total_charges= charges["total_charges"]
    net_pnl      = gross_pnl - total_charges
    charge_pct   = (total_charges / abs(gross_pnl) * 100) if gross_pnl != 0 else 0

    return {
        "buy_price":     buy_price,
        "sell_price":    sell_price,
        "quantity":      quantity,
        "buy_value":     round(buy_value, 2),
        "sell_value":    round(sell_value, 2),
        "gross_pnl":     round(gross_pnl, 2),
        "charges":       charges,
        "total_charges": round(total_charges, 2),
        "net_pnl":       round(net_pnl, 2),
        "charge_pct_of_gross": round(charge_pct, 1),
        "warning":       _pnl_warning(charge_pct),
    }


def _pnl_warning(charge_pct: float) -> str:
    if charge_pct >= 30:
        return "RED"      # charges eating >30% of profit
    if charge_pct >= 15:
        return "YELLOW"
    return "GREEN"


def scale_charges_table(avg_trade_value: float = 10000) -> list[dict]:
    """Returns charge breakdown at 100/500/1000/5000 trades/day."""
    rows = []
    for trades in [100, 500, 1000, 5000]:
        daily_buy  = avg_trade_value * trades
        daily_sell = avg_trade_value * trades
        c = calculate_delivery_charges(daily_buy, daily_sell)
        rows.append({
            "trades_per_day":  trades,
            "daily_turnover":  round(daily_buy + daily_sell, 0),
            "brokerage":       c["brokerage"],
            "stt":             c["stt"],
            "dp_charge":       trades * 20,            # ₹20 per sell trade
            "other_charges":   round(c["nse_txn"] + c["stamp_duty"] + c["sebi_fee"] + c["gst"], 0),
            "total_per_day":   round(c["total_charges"] + (trades * 20), 0),
            "total_per_month": round((c["total_charges"] + (trades * 20)) * 22, 0),
            "total_per_year":  round((c["total_charges"] + (trades * 20)) * 252, 0),
        })
    return rows
