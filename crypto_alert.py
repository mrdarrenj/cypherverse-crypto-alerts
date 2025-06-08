import os
import requests
from datetime import datetime
import math
import time
import statistics
import pytz
from telegram import Bot

# Load Telegram credentials from GitHub Secrets
TELEGRAM_BOT_TOKEN = os.environ.get("8018409461:AAEvnjpkSSa482DHbnuNb_dLfukla_EJoVU")
TELEGRAM_USER_ID = os.environ.get("6584100075")

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Define your watchlist
WATCHLIST = ["BTC-USD", "ETH-USD", "XRP-USD", "DOGE-USD", "SOL-USD"]

# Utility functions
def get_coinbase_data(symbol):
    url = f"https://api.coinbase.com/v2/prices/{symbol}/spot"
    response = requests.get(url)
    price = float(response.json()["data"]["amount"])
    return price

def get_historic_prices(symbol, granularity=86400):
    url = f"https://api.exchange.coinbase.com/products/{symbol}/candles?granularity={granularity}"
    response = requests.get(url)
    candles = response.json()
    closes = [c[4] for c in candles]
    closes.reverse()
    return closes

def calculate_rsi(data, period=14):
    gains = []
    losses = []
    for i in range(1, len(data)):
        change = data[i] - data[i-1]
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def calculate_macd(prices):
    def ema(data, window):
        k = 2 / (window + 1)
        ema_data = [sum(data[:window]) / window]
        for price in data[window:]:
            ema_data.append(price * k + ema_data[-1] * (1 - k))
        return ema_data
    ema_12 = ema(prices, 12)
    ema_26 = ema(prices, 26)
    macd_line = [a - b for a, b in zip(ema_12[-len(ema_26):], ema_26)]
    signal_line = ema(macd_line, 9)
    return macd_line[-1], signal_line[-1]

def identify_support_resistance(prices):
    avg = statistics.mean(prices)
    std_dev = statistics.stdev(prices)
    support = round(avg - std_dev, 2)
    resistance = round(avg + std_dev, 2)
    return support, resistance

# Time formatting
now = datetime.now(pytz.timezone("US/Central"))
timestamp = now.strftime("%A %B %d • %I:%M %p CST")

# Build alert message
messages = [f"🧠 *CYPHERVERSE DAILY ALERT*\n📅 {timestamp}\n"]

for symbol in WATCHLIST:
    try:
        ticker = symbol.split("-")[0]
        price = get_coinbase_data(symbol)
        closes = get_historic_prices(symbol)
        rsi = calculate_rsi(closes)
        macd, signal = calculate_macd(closes)
        support, resistance = identify_support_resistance(closes)

        trend = "📈 Bullish" if macd > signal and rsi < 70 else "📉 Bearish" if macd < signal and rsi > 30 else "🔁 Consolidating"

        message = f"""
💎 *{ticker}*
💰 Price: `${price:.2f}`
📊 RSI: {rsi}  
📉 MACD: {macd:.4f} | Signal: {signal:.4f}
🧭 Trend: {trend}
📉 Support: `${support}` | 🧱 Resistance: `${resistance}`
        """.strip()

        messages.append(message)
        time.sleep(1)  # to avoid rate limits

    except Exception as e:
        messages.append(f"⚠️ Error fetching {symbol}: {str(e)}")

# Send to Telegram
final_alert = "\n\n".join(messages)
bot.send_message(chat_id=TELEGRAM_USER_ID, text=final_alert, parse_mode='Markdown')
