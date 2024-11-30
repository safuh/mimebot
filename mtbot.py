import time
import logging
from brokerapi import get_broker
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

timeframe='M30'
forex_symbols = ['EURUSD', 'GBPUSD', 'USDJPY','AUDUSD','USDCAD','EURGBP', 'NZDUSD', 'USDCHF','XAUUSD']
broker=get_broker()
account_balance=1000
rsi_thresholds={'oversold_threshold':30,
                'overbought_threshold': 70,
                'stochastic_buy_threshold':20,
                'stochastic_sell_threshold': 80}
from TraderExe import TradeExecutor

def main():
    risk_percentage=0.1
    while True:
        try:
            for symbol in forex_symbols:
                #logging.info(f"Analyzing {symbol}")
                symbol_info = broker.get_symbol_info(symbol)
                #logging.info(f"{symbol} Specs - Min Volume: {symbol_info.volume_min}, Max Volume: {symbol_info.volume_max}, Step: {symbol_info.volume_step}")
                tradeExecutor=TradeExecutor(broker,broker.fetch_forex_data(symbol,timeframe),**rsi_thresholds)
                latest_signal = tradeExecutor.df['signal'].iloc[-1]
                logging.info(f"Latest signal for {symbol}: {latest_signal}")
                if latest_signal != 0:
                    logging.info(f"Latest signal for {symbol}: {latest_signal}")
                    tradeExecutor.execute_trade(symbol, latest_signal,risk_percentage)
                time.sleep(5)
                # Wait before analyzing the next symbol
                #results = backtest(df, account_balance, risk_percentage, stop_loss_pips, take_profit_pips, pip_value,symbol)
                #logging.info(f"Backtest Results for {symbol}: {results}")

            # Wait for the next cycle
            time.sleep(5)
        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            break
if __name__ =="__main__":
    main()