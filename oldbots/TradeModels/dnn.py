import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from fetch_ohlcv import exchange, fetch_data
from indicators import calculate_indicators
# Define parameters
n_epochs = 50
batch_size = 32

# Preprocess data
def prepare_data(df):
    df=calculate_indicators(df)

    df.dropna(inplace=True)
    X = df[['close', 'SMA_short', 'SMA_long', 'RSI', 'Momentum', 'Stochastic_RSI']].values
    y = np.where(df['signal'] == 1, 1, 0)  # Binary classification: 1 for buy, 0 for sell/hold

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Build DNN model
def build_dnn_model(input_shape):
    model = tf.keras.models.Sequential([
        tf.keras.layers.Dense(128, activation='relu', input_shape=input_shape),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

# Train model
df = fetch_data('BTC/USDT', '5m')
X_train, X_test, y_train, y_test = prepare_data(df)
dnn_model = build_dnn_model((X_train.shape[1],))
dnn_model.fit(X_train, y_train, epochs=n_epochs, batch_size=batch_size, validation_data=(X_test, y_test))

# Predict signals
predictions = dnn_model.predict(X_test)
trade_signals = [1 if pred > 0.5 else -1 for pred in predictions.flatten()]
