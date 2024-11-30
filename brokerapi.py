import MetaTrader5 as mt5 # type: ignore
import logging
import time
import pandas as pd
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BrokerAPI:
    def __init__(self, server, login, password):
        self.server = server
        self.login = login
        self.password = password
        self.initialize()

    def initialize(self):
        """
        Initialize the MetaTrader5 connection.
        """
        #login=self.login, password=self.password, server=self.server
        if not mt5.initialize():
            error = mt5.last_error()
            raise ConnectionError(f"Failed to initialize MetaTrader5. Error: {error}")
        else:
            print(mt5.terminal_info())
            print(mt5.version())
            auth=mt5.login(self.login, password=self.password,server=self.server)
            if auth:
                print(mt5.account_info())
                print("Show account_info()._asdict():")
                account_info_dict = mt5.account_info()._asdict()
                print("Trade allowed={}".format(account_info_dict['trade_allowed']))
            else:
                print("failed to connect at account #{}, error code: {}".format(self.login, mt5.last_error()))
        logging.info("MetaTrader5 initialized successfully.")
    
    def shutdown(self):
        """
        Shutdown the MetaTrader5 connection.
        """
        mt5.shutdown()
        logging.info("MetaTrader5 connection closed.")

    def get_ticker(self, symbol):
        """
        Get the current bid and ask prices for a Forex symbol.

        Parameters:
            symbol (str): The Forex symbol (e.g., 'EURUSD').

        Returns:
            dict: Contains 'bid' and 'ask' prices.
        """
        selected=mt5.symbol_select(symbol,True)
        if not selected:
            print("Failed to select symbol")
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            error = mt5.last_error()
            raise ValueError(f"Failed to retrieve ticker for {symbol}. Error: {error}")
        return {"bid": tick.bid, "ask": tick.ask}
    def get_symbol_info(self,symbol):
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            raise ValueError(f"Symbol {symbol} information is unavailable.")
        return symbol_info
    def create_market_order(self, symbol, action, volume,sl,tp):
        """
        Place a market order (buy or sell).

        Parameters:
            symbol (str): The Forex symbol (e.g., 'EURUSD').
            action (str): 'buy' or 'sell'.
            volume (float): The volume of the order.

        Returns:
            dict: Result of the order execution.
        """
        if action not in ['buy', 'sell']:
            raise ValueError("Action must be 'buy' or 'sell'.")
        selected=mt5.symbol_select(symbol,True)
        if not selected:
            print("Failed to select symbol")
        symbol_info = self.get_symbol_info(symbol)
        stop_level =  symbol_info.trade_stops_level * symbol_info.point if symbol_info.trade_stops_level else 0
        order_type = mt5.ORDER_TYPE_BUY if action == 'buy' else mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).ask if action == 'buy' else mt5.symbol_info_tick(symbol).bid
        if sl and abs(price - sl) < stop_level:
            logging.info(f"Invalid SL:->{sl} Must be at least {stop_level} away from price.")
        if tp and abs(tp - price) < stop_level:
            logging.info(f"Invalid TP:->{tp} Must be at least {stop_level} away from price.")
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl":sl,
            "tp":tp,
            "deviation": 20,
            "magic": 234000,
            "comment": f"Auto-trade {action}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        logging.info(f"Order request: {request}")
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error = mt5.last_error()
            raise ValueError(f"Order failed. Retcode: {result.retcode}, Error: {error}")

        logging.info(f"Order executed successfully: {result}")
        return result
    def create_stop_limit_order(self, symbol, action, volume, sl, tp,price):
        order_type = mt5.ORDER_TYPE_BUY_STOP_LIMIT if action == 'buy' else mt5.ORDER_TYPE_SELL_STOP_LIMIT
        symbol_info = self.get_symbol_info(symbol)
        stop_level =  symbol_info.trade_stops_level * symbol_info.point if symbol_info.trade_stops_level else 0
        
        if sl and abs(price - sl) < stop_level:
            logging.info(f"Invalid SL:->{sl} Must be at least {stop_level} away from price.")
        if tp and abs(tp - price) < stop_level:
            logging.info(f"Invalid TP:->{tp} Must be at least {stop_level} away from price.")
        
        request = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": f"Auto-trade {action} stop-limit",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        logging.info(f"Stop-limit order request: {request}")
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise ValueError(f"Order failed. Retcode: {result.retcode}, Error: {mt5.last_error()}")
        logging.info(f"Stop-limit order placed successfully: {result}")
        return result

    def get_pip_value(self,symbol, lot_size=100000):
        try:
            symbol_info=self.get_symbol_info(symbol)
            price = mt5.symbol_info_tick(symbol).bid
            point = symbol_info.point
            if symbol.endswith("USD"):  # USD is the quote currency
                pip_value = (point * lot_size) / price
            else:
                quote_currency = symbol[3:]  # Extract the quote currency
                base_currency = symbol[:3]  # Extract the base currency
                conversion_symbol = f"{quote_currency}USD" if quote_currency != "USD" else f"USD{base_currency}"
                conversion_rate = mt5.symbol_info_tick(conversion_symbol).bid if mt5.symbol_info(conversion_symbol) else 1.0
                pip_value = (point * lot_size) / price * conversion_rate
            return round(pip_value, 5)
        except Exception as e:
            logging.error(f"Error calculating pip value for {symbol}: {e}")
            return None
    def fetch_forex_data(self,symbol, timeframe,n_bars=1000):
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
        # Check if the timeframe is valid
        if timeframe not in timeframe_map:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        rates = mt5.copy_rates_from_pos(symbol, timeframe_map[timeframe], 0, n_bars)
        if rates is None:
            raise ValueError(f"Failed to retrieve data for symbol: {symbol}. Error: {mt5.last_error()}")
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')  # Convert timestamp to datetime
        df = df.rename(columns={
            'time': 'timestamp',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'tick_volume': 'volume'
        })
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]    
        return df

def get_broker():
    server = "MetaQuotes-Demo"
    login = 88217430
    password = "*z6yQwHh"
    return BrokerAPI(server, login, password)
def get_all_forex_symbols():
    all_symbols = mt5.symbols_get()
    forex_symbols = [symbol.name for symbol in all_symbols if "/" in symbol.name or len(symbol.name) == 6]
    return forex_symbols

