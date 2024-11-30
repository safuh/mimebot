import random
import pandas as pd
import numpy as np
import time
from constants import *
from fetch_ohlcv import exchange,fetch_data
from indicators import calculate_indicators


def apply_strategy(df):
    # Calculate indicators
    df=calculate_indicators(df)
    df['signal'] = 0

    # Buy signal (condition)
    df['signal'] = np.where(
        (df['RSI'] < oversold_threshold) &
        (df['Momentum'] > 0) &
        (df['SMA_short'] > df['SMA_long']) &
        (df['Stochastic_RSI'] < 20), 1, df['signal'])

    # Sell signal (condition)
    df['signal'] = np.where(
        (df['RSI'] > overbought_threshold) &
        (df['Momentum'] < 0) &
        (df['SMA_short'] < df['SMA_long']) &
        (df['Stochastic_RSI'] > 80), -1, df['signal'])

    return df

# Execute trade based on signal
def execute_trade(signal, symbol, amount):
    if signal == 1:
        print(f"Buying {amount} of {symbol}")
        exchange.create_market_buy_order(symbol, amount)  # Uncomment this to enable live trading
    elif signal == -1:
        print(f"Selling {amount} of {symbol}")
        exchange.create_market_sell_order(symbol, amount)  # Uncomment this to enable live trading

# Main loop
while True:
    symbol=random.choice(symbols)
    try:
        # Fetch market data
        df = fetch_data(symbol, timeframe)

        # Apply the strategy
        df = apply_strategy(df)

        # Get the latest signal
        latest_signal = df['signal'].iloc[-1]
        # Execute trade based on the latest signal
        #execute_trade(latest_signal, symbol, amount)

        # Wait for the next interval
        time.sleep(60)  # Sleep for 1 minute between checks
        break

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(60)