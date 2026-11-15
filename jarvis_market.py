
"""
jarvis_market.py - Yahoo Finance market data for Jarvis.
Supports Indian stocks, US stocks, indices and cryptocurrency.
"""

import urllib.request
import urllib.parse
import json
import ssl

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    CTX = ssl.create_default_context()

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
)

DEFAULT_TICKERS = {
    "^NSEI": "Nifty 50",
    "^BSESN": "Sensex",
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "TCS",
    "INFY.NS": "Infosys",
    "HDFCBANK.NS": "HDFC Bank",
    "NVDA": "Nvidia",
    "AAPL": "Apple",
    "BTC-USD": "Bitcoin",
}


def _fetch_chart(symbol, range_period="5d", interval="15m"):
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + urllib.parse.quote(symbol)
        + f"?range={range_period}&interval={interval}"
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(
            request, timeout=10, context=CTX
        ) as response:
            data = json.loads(
                response.read().decode("utf-8", "ignore")
            )

        results = data.get("chart", {}).get("result", [])

        if not results:
            return None

        return results[0]

    except Exception as error:
        print(f"[Market Data Error - {symbol}]: {error}")
        return None


def analyze_ticker(symbol):
    chart = _fetch_chart(symbol)

    if not chart:
        return None

    meta = chart.get("meta", {})

    price = meta.get("regularMarketPrice")
    previous = (
        meta.get("chartPreviousClose")
        or meta.get("previousClose")
        or price
    )

    if price is None:
        return None

    try:
        price = float(price)
        previous = float(previous)
    except (TypeError, ValueError):
        return None

    change = price - previous
    pct_change = (
        (change / previous) * 100 if previous else 0.0
    )

    currency = meta.get("currency", "USD")
    currency_symbol = "₹" if currency == "INR" else "$"

    quotes = (
        chart.get("indicators", {})
        .get("quote", [{}])[0]
        .get("close", [])
    )

    valid_quotes = [
        float(value)
        for value in quotes
        if value is not None
    ]

    signal = "HOLD"
    reason = "No strong short-term trend detected."

    if len(valid_quotes) >= 10:
        sma_short = sum(valid_quotes[-5:]) / 5
        sma_long = sum(valid_quotes[-15:]) / min(
            len(valid_quotes), 15
        )

        if (
            price > sma_short
            and sma_short > sma_long
            and pct_change > 0.5
        ):
            signal = "STRONG BUY"
            reason = "Positive short-term momentum."

        elif price > sma_short and pct_change >= 0:
            signal = "BUY / ACCUMULATE"
            reason = "Price is above the short-term average."

        elif (
            price < sma_short
            and sma_short < sma_long
            and pct_change < -0.5
        ):
            signal = "STRONG SELL"
            reason = "Negative short-term momentum."

        elif price < sma_short:
            signal = "SELL / TAKE PROFIT"
            reason = "Price is below the short-term average."

    return {
        "symbol": symbol,
        "name": DEFAULT_TICKERS.get(symbol, symbol),
        "price": round(price, 2),
        "change": round(change, 2),
        "pct_change": round(pct_change, 2),
        "currency": currency_symbol,
        "signal": signal,
        "reason": reason,
        "high": meta.get("regularMarketDayHigh", price),
        "low": meta.get("regularMarketDayLow", price),
    }


def market_briefing():
    reports = []

    for symbol in [
        "^NSEI",
        "RELIANCE.NS",
        "NVDA",
        "BTC-USD",
    ]:
        data = analyze_ticker(symbol)

        if data:
            direction = (
                "up" if data["pct_change"] >= 0 else "down"
            )

            reports.append(
                f"{data['name']} is at "
                f"{data['currency']}{data['price']:,.2f}, "
                f"{direction} {abs(data['pct_change']):.2f}%. "
                f"Technical indicator: {data['signal']}."
            )

    if not reports:
        return "Market data is currently unavailable."

    return " ".join(reports)


def get_market_watchlist():
    results = []

    for symbol in DEFAULT_TICKERS:
        data = analyze_ticker(symbol)

        if data:
            results.append(data)

    return results


if __name__ == "__main__":
    print("Testing Jarvis Market Intelligence...")
    print(market_briefing())
