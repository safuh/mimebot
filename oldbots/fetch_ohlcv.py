from exchanger import exchange
import MetaTrader5 as mt5 # type: ignore
import pandas as pd

def fetch_data(symbol, timeframe, limit=1000):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df
def fetch_forex_data(symbol, timeframe,n_bars=1000):
    # Implement data fetching logic here
    # Map timeframes
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

    # Initialize MetaTrader5 connection
    if not mt5.initialize():
        raise ConnectionError(f"MetaTrader5 initialization failed. Error: {mt5.last_error()}")
    
    # Get historical data
    rates = mt5.copy_rates_from_pos(symbol, timeframe_map[timeframe], 0, n_bars)
    if rates is None:
        raise ValueError(f"Failed to retrieve data for symbol: {symbol}. Error: {mt5.last_error()}")
    
    # Shutdown MetaTrader5 after fetching data
    mt5.shutdown()

    # Convert to DataFrame
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
    
    # Keep only required columns
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    return df
