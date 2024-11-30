from constants import *

# Calculate indicators
def calculate_indicators(df):
    df['SMA_short'] = df['close'].rolling(window=sma_short_window).mean()
    df['SMA_long'] = df['close'].rolling(window=sma_long_window).mean()
    df['RSI'] = calculate_rsi(df, rsi_period)
    df['Momentum'] = df['close'].diff(momentum_period)
    df['Stochastic_RSI'] = calculate_stochastic_rsi(df, stochastic_period)
    return df

def calculate_rsi(df, period):
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_stochastic_rsi(df, period):
    rsi = calculate_rsi(df, period)
    stoch_rsi = (rsi - rsi.rolling(window=period).min()) / (rsi.rolling(window=period).max() - rsi.rolling(window=period).min())
    return stoch_rsi * 100
