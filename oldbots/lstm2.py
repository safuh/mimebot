import time
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import logging
from fetch_ohlcv import fetch_forex_data
from brokerapi import get_broker
broker=get_broker()
timeframe='M5'
forex_symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
oversold_threshold = 30
overbought_threshold = 70
stochastic_buy_threshold = 20

stochastic_sell_threshold = 80
risk_percentage = 0.01  # 1% per trade
stop_loss_pips = 10
pip_value = 0.0001
interval = 60  # seconds
account_balance=100

# Prepare data for LSTM
def prepare_lstm_data(df, sequence_length=50):
    features = ['RSI', 'Momentum', 'SMA_short', 'SMA_long', 'Stochastic_RSI']
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(df[features])
    
    X, y = [], []
    for i in range(sequence_length, len(scaled_data)):
        X.append(scaled_data[i-sequence_length:i])  # Sequence of features
        y.append(1 if df['Close'].iloc[i] > df['Close'].iloc[i-1] else 0)  # Label: 1 for up, 0 for down

    return np.array(X), np.array(y), scaler
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import LSTM, Dense, Dropout # type: ignore

def build_lstm_model(input_shape):
    model = Sequential()
    model.add(LSTM(units=50, return_sequences=True, input_shape=input_shape))
    model.add(Dropout(0.2))
    model.add(LSTM(units=50, return_sequences=False))
    model.add(Dropout(0.2))
    model.add(Dense(units=1, activation='sigmoid'))  # Output: Probability of price going up
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import EarlyStopping # type: ignore

# Split data and train
df = fetch_forex_data(forex_symbols[0], timeframe)
X, y, scaler = prepare_lstm_data(df)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = build_lstm_model(input_shape=(X_train.shape[1], X_train.shape[2]))
early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=50, batch_size=32, callbacks=[early_stopping])

# Save the model
model.save("lstm_trading_model.h5")
from tensorflow.keras.models import load_model # type: ignore

# Load trained model
model = load_model("lstm_trading_model.h5")

def predict_signal(df, model, scaler, sequence_length=50):
    features = ['RSI', 'Momentum', 'SMA_short', 'SMA_long', 'Stochastic_RSI']
    latest_data = df[features].iloc[-sequence_length:].values
    scaled_data = scaler.transform(latest_data)
    X_input = np.array([scaled_data])  # Add batch dimension
    prediction = model.predict(X_input)[0][0]  # Output probability

    # Convert probability to signal
    if prediction > 0.6:  # Confidence threshold for buy
        return 1
    elif prediction < 0.4:  # Confidence threshold for sell
        return -1
    return 0  # Hold
def apply_strategy(df):
    signal = predict_signal(df, model, scaler)
    logging.info(f"Predicted signal: {signal}")
    return signal

def main():
    while True:
        try:
            for symbol in forex_symbols:
                logging.info(f"Analyzing {symbol}")

                # Fetch market data
                df = fetch_forex_data(symbol, timeframe)

                # Predict signal using LSTM
                signal = apply_strategy(df)

                # Execute trade based on the prediction
                if signal != 0:
                    #execute_trade(symbol, risk_percentage, signal)
                    pass
                time.sleep(5)

            # Wait for the next cycle
            time.sleep(interval)

        except Exception as e:
            logging.error(f"Error in main loop: {e}")
            time.sleep(60)
