import numpy as np
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
from indicators import calculate_indicators,calculate_dynamic_sl_tp
from brokerapi import BrokerAPI
class TradeExecutor:
    def __init__(self,broker,df,oversold_threshold,overbought_threshold,stochastic_sell_threshold,stochastic_buy_threshold):
        self.oversold_threshold=oversold_threshold
        self.overbought_threshold=overbought_threshold
        self.stochastic_sell_threshold=stochastic_sell_threshold
        self.stochastic_buy_threshold=stochastic_buy_threshold
        self.broker=broker
        self.df=self.apply_strategy(df)
    def apply_strategy(self,df):
        df = calculate_indicators(df)
        df = df.dropna(subset=['RSI', 'Momentum', 'SMA_short', 'SMA_long', 'Stochastic_RSI']).copy()
        df['buy_signal'] = np.where(
            (df['RSI'] < self.oversold_threshold) &
            (df['SMA_short'] > df['SMA_long']) &
            (df['Stochastic_RSI'] < self.stochastic_buy_threshold), 
            1, 0)
        df['sell_signal'] = np.where(
            (df['RSI'] > self.overbought_threshold) &
            (df['SMA_short'] < df['SMA_long']) &
            (df['Stochastic_RSI'] > self.stochastic_sell_threshold), 
            -1, 0)
        df['signal'] = df['buy_signal'] + df['sell_signal']
        #logging.info(f"Buy signals: {len(df[df['signal'] == 1])}")
        #logging.info(f"Sell signals: {len(df[df['signal'] == -1])}")
        #logging.info(f"All Buy/Sell signals:\n{df[df['signal']!=0].tail()}\n\n")
        return df
    def execute_trade(self,symbol, signal,risk_percentage,stop_loss_percent=0.0025,take_profit_percent=0.01,):
        try:
            ticker = self.broker.get_ticker(symbol)
            last_price = ticker['bid'] if signal == -1 else ticker['ask']
            pointer = self.broker.get_symbol_info(symbol)
            point=pointer.point
            #position_size = calculate_position_size(account_balance, risk_percentage, stop_loss_pips, pip_value,symbol)
            position_size=0.1
            #sl_price, tp_price = calculate_dynamic_sl_tp(self.df, last_price, signal, atr_multiplier=1.5)
            if signal == 1:
                sl_price = last_price * (1 - stop_loss_percent)
                tp_price = last_price * (1 + take_profit_percent)
                #sl_price = last_price - (stop_loss_pips * point)
                #tp_price = last_price + (stop_loss_pips * take_profit_ratio * point)
                logging.info(f"Placing Buy order: {symbol}, Size: {position_size}")
                self.broker.create_market_order(symbol, 'buy', position_size,sl_price,tp_price)
                #exit_price = last_price + (take_profit_pips * pip_value)
                #trade_profit = (exit_price - last_price) * position_size
                #logging.info(f"Simulated Buy: Entry={last_price}, Exit={exit_price}, Profit=${trade_profit:.2f}")
            elif signal == -1:
                sl_price = last_price * (1 + stop_loss_percent)
                tp_price = last_price * (1 - take_profit_percent)
                #sl_price = last_price + (stop_loss_pips * point)
                #tp_price = last_price - (stop_loss_pips * take_profit_ratio * point)
                logging.info(f"Placing Sell order: {symbol}, Size: {position_size}")
                self.broker.create_market_order(symbol, 'sell', position_size,sl_price,tp_price)
                #exit_price = last_price - (take_profit_pips * pip_value)
                #trade_profit = (last_price - exit_price) * position_size
                #logging.info(f"Simulated Sell: Entry={last_price}, Exit={exit_price}, Profit=${trade_profit:.2f}")
            #total_profit += trade_profit
            #trade_count += 1
            #if trade_profit > 0:
            #    winning_trades += 1
            #else:
            #    losing_trades += 1
        except Exception as e:
            logging.error(f"Trade execution failed: {e}")
