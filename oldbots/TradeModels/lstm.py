import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import Dense, LSTM, Dropout # type: ignore
from sklearn.preprocessing import MinMaxScaler
from indicators import calculate_indicators
from fetch_ohlcv import exchange, fetch_data

# Load data and calculate technical indicators
def load_data():
    df = fetch_data('BTC/USDT', '5m')  # Replace with data fetching function
    df= calculate_indicators(df)
    df.dropna(inplace=True)
    return df

df = load_data()

# Prepare the dataset for LSTM model
def preprocess_data(df, lookback=50):
    scaler = MinMaxScaler(feature_range=(0, 1))
    data = df[['close', 'SMA_short', 'SMA_long', 'RSI', 'Momentum', 'Stochastic_RSI']]
    data_scaled = scaler.fit_transform(data)
    
    X, y = [], []
    for i in range(lookback, len(data_scaled)):
        X.append(data_scaled[i-lookback:i-1])  # Take 'lookback' number of past time steps
        y.append(data_scaled[i, 0])  # Predict the close price at the next time step

    X, y = np.array(X), np.array(y)
    return X, y, scaler

# Prepare data
lookback = 50
X, y, scaler = preprocess_data(df, lookback)

# Build LSTM model
def create_lstm_model(input_shape):
    model = Sequential()
    model.add(LSTM(64, return_sequences=True, input_shape=input_shape))
    model.add(Dropout(0.2))
    model.add(LSTM(64, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(64, activation="relu"))
    model.add(Dense(1, activation="linear"))  # Linear activation for price prediction
    model.compile(optimizer="adam", loss="mse")
    return model

input_shape = (X.shape[1], X.shape[2])
model = create_lstm_model(input_shape)
model.summary()

# Train the LSTM model
epochs = 50
batch_size = 64
model.fit(X, y, epochs=epochs, batch_size=batch_size, validation_split=0.2, verbose=1)

# Trading bot logic
initial_balance = 100
balance = initial_balance
position = 0  # 1 if holding a position, 0 otherwise
entry_price = 0

def make_trading_decision(predicted_price, current_price):
    global balance, position, entry_price
    if predicted_price > current_price and position == 0:
        # Buy signal
        entry_price = current_price
        position = 1
        print(f"Buying at price {current_price}")
    elif predicted_price < current_price and position == 1:
        # Sell signal
        profit = current_price - entry_price
        balance += profit
        position = 0
        print(f"Selling at price {current_price}, Profit: {profit}")

# Simulate trading
def simulate_trading(df, lookback, model, scaler):
    global balance, position
    for i in range(lookback, len(df) - 1):
        current_data = df[['close', 'SMA_short', 'SMA_long', 'RSI', 'Momentum', 'Stochastic_RSI']].iloc[i-lookback:i-1]
        current_price = df['close'].iloc[i]
        
        # Prepare data for LSTM prediction
        current_data_scaled = scaler.transform(current_data)
        current_data_scaled = np.expand_dims(current_data_scaled, axis=0)
        
        # Predict the next price
        predicted_scaled_price = model.predict(current_data_scaled)
        predicted_price = scaler.inverse_transform([[predicted_scaled_price[0][0], 0, 0, 0, 0, 0]])[0][0]
        
        # Make trading decision based on predicted price
        make_trading_decision(predicted_price, current_price)

    # Final balance and position check
    if position == 1:
        # Close the position if still open
        final_price = df['close'].iloc[-1]
        profit = final_price - entry_price
        balance += profit
        position = 0
        print(f"Closing position at end of period, Final Profit: {profit}")
    
    print(f"Final Balance: {balance}")

# Run simulation
simulate_trading(df, lookback, model, scaler)
