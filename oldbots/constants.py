# Parameters
symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']  # List of top cryptos
timeframe = '1h'  # 5-minute candlesticks
trade_amount = 0.001  # Adjust according to balance and symbol
rsi_period = 7
#Shorter periods (e.g., 7,14) make RSI more responsive to price changes but increase noise.
#Longer periods (e.g., 21) smooth out signals but may delay entries/exits.

sma_short_window = 10
sma_long_window = 20
#Short SMA: [3, 5, 10].Maintain a reasonable gap between short and long SMA to reduce noise and ensure meaningful crossovers.
#Long SMA: [10, 20, 50].

stochastic_period = 5
#[5, 10, 14].
#Shorter periods make the stochastic indicator more reactive, which is suitable for scalping.
#Longer periods reduce signal frequency but improve reliability.
overbought_threshold = 65
oversold_threshold = 35
momentum_period = 5 #5-20

# Risk management
stop_loss_percent = 0.02  # 2% stop loss
take_profit_percent = 0.03  # 3% take profit
trailing_stop_percent = 0.01  # 1% trailing stop

stochastic_buy_threshold = 25
stochastic_sell_threshold = 75