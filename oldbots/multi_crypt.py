import pandas as pd
import numpy as np
import time
import logging
from fetch_ohlcv import exchange, fetch_data
from indicators import calculate_indicators
from constants import *
#logging for better debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Apply strategy-generate signal
def apply_strategy(df):
    df = calculate_indicators(df)
    #logging.info(f"NaN values per indicator:\n{df[['RSI', 'Momentum', 'SMA_short', 'SMA_long', 'Stochastic_RSI']].isna().sum()}")
    
    df = df.dropna(subset=['RSI', 'Momentum', 'SMA_short', 'SMA_long', 'Stochastic_RSI']).copy()
    df['signal'] = 0
    #logging.info(f"After dropping NaNs, data size: {len(df)}")
    #logging.info(f"After dropping NaNs, data size: {df.tail()}")
    # Initialize buy and sell signals
    df['buy_signal'] = np.where(
    (df['RSI'] < oversold_threshold) &
    #(df['Momentum'] > 0) &
    (df['SMA_short'] > df['SMA_long']) &
    (df['Stochastic_RSI'] < stochastic_buy_threshold), 
    1, 
    0  # No buy signal
)

    df['sell_signal'] = np.where(
    (df['RSI'] > overbought_threshold) &
    #(df['Momentum'] < 0) &
    (df['SMA_short'] < df['SMA_long']) &
    (df['Stochastic_RSI'] > stochastic_sell_threshold), 
    -1, 
    0  # No sell signal
)

# Combine signals
    df['signal'] = df['buy_signal'] + df['sell_signal']
    # Buy signal ,
    #df.loc[:,'signal'] = np.where(
    #    (df['RSI'] < oversold_threshold) &
        #(df['Momentum'] > 0) &
    #    (df['SMA_short'] > df['SMA_long']) &
    #    (df['Stochastic_RSI'] < stochastic_buy_threshold), 1, df['signal'])
    #logging.info(f"Buy signal condition:\n{df[['RSI', 'Momentum', 'SMA_short', 'SMA_long', 'Stochastic_RSI', 'signal']].tail()}")
    # Sell signal
    #df.loc[:,'signal'] = np.where(
    #    (df['RSI'] > overbought_threshold) &
        #(df['Momentum'] < 0) &
    #    (df['SMA_short'] < df['SMA_long']) &
    #    (df['Stochastic_RSI'] > stochastic_sell_threshold), -1, df['signal'])
    #logging.info(f"Sell signal condition:\n{df[['RSI', 'Momentum', 'SMA_short', 'SMA_long', 'Stochastic_RSI', 'signal']].tail()}")
    #df['signal'] = df['buy_signal'] + df['sell_signal']
    logging.info(f"Buy signals generated: {len(df[df['signal'] == 1])}")
    logging.info(f"Sell signals generated: {len(df[df['signal'] == -1])}")
    logging.info(f"All Buy/Sell signals:\n{df[df['signal']!=0].tail()}\n\n")
    return df

def execute_trade(symbol, amount, signal):
    last_price = exchange.fetch_ticker(symbol)['last']
    
    if signal == 1:
        logging.info(f"Buying {amount} of {symbol}")
        order = exchange.create_market_buy_order(symbol, amount)
        stop_loss_price = last_price * (1 - stop_loss_percent)
        take_profit_price = last_price * (1 + take_profit_percent)
        
        # Place stop-loss and take-profit orders
        exchange.create_order(symbol, 'STOP_LOSS_LIMIT', 'sell', amount, stop_loss_price)
        exchange.create_order(symbol, 'TAKE_PROFIT_LIMIT', 'sell', amount, take_profit_price)

    elif signal == -1:
        logging.info(f"Selling {amount} of {symbol}")
        order = exchange.create_market_sell_order(symbol, amount)
        stop_loss_price = last_price * (1 + stop_loss_percent)
        take_profit_price = last_price * (1 - take_profit_percent)
        
        # Place stop-loss and take-profit orders
        exchange.create_order(symbol, 'STOP_LOSS_LIMIT', 'buy', amount, stop_loss_price)
        exchange.create_order(symbol, 'TAKE_PROFIT_LIMIT', 'buy', amount, take_profit_price)

# Main loop
def main():
    while True:
        try:
            for symbol in symbols:
                logging.info(f"Analyzing {symbol}\n")
                
                # Fetch market data
                df = fetch_data(symbol, timeframe)
                #logging.info(f'ohlcv data for {symbol} => ${df.tail()}')


                df = apply_strategy(df)
                #logging.info(f'indicators data for {symbol} => ${df.tail()}')
                #logging.info(f'signal data for {symbol}=> ${df['signal'].tail()}')


                # Get the latest signal
                latest_signal = df['signal'].iloc[-1]
                logging.info(f"Latest signal for {symbol}: {latest_signal}->\n{df[['timestamp','buy_signal','sell_signal','signal']].tail(1)} \n\n")                
                # Execute trade based on the latest signal
                #execute_trade(symbol, trade_amount, latest_signal)
                
                # Wait a bit before next symbol to respect API rate limits
                time.sleep(5)

            # Wait for the next interval
            time.sleep(60)

        except Exception as e:
            logging.error(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
