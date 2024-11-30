import numpy as np
import pandas as pd
import logging
from fetch_ohlcv import exchange, fetch_data # type: ignore
from indicators import calculate_indicators # type: ignore
from constants import *

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# Load and preprocess data
def load_data(symbol, timeframe):
    df = calculate_indicators(fetch_data(symbol, timeframe))
    df.dropna(inplace=True)
    return df

# Initialize parameters
def initialize_parameters():
    params = {
        "n_actions": 3,  # Actions: [Hold, Buy, Sell]
        "n_states": 50,  # Discretize states
        "alpha": 0.1,    # Learning rate
        "gamma": 0.95,   # Discount factor
        "epsilon": 1.0,  # Exploration rate
        "epsilon_min": 0.1,
        "epsilon_decay": 0.995,
        "initial_balance": 1000
    }
    params["state_space"] = np.linspace(-1, 1, params["n_states"])  # State discretization
    return params

# Discretize state
def get_state(row, state_space):
    sma_diff = row['SMA_short'] - row['SMA_long']
    rsi = row['RSI']
    momentum = row['Momentum']
    combined_score = (sma_diff + rsi / 100 + momentum / 100) / 3
    state_index = np.digitize(combined_score, state_space) - 1
    return min(max(state_index, 0), len(state_space) - 1)

# Take action and calculate rewards
def take_action(action, step, position, balance, entry_price, df):
    current_price = df.iloc[step]['close']
    reward = 0

    if action == 1 and position == 0:  # Buy
        position = 1
        entry_price = current_price
        reward = -1  # Small entry cost

    elif action == 2 and position == 1:  # Sell
        profit = current_price - entry_price
        reward = profit
        balance += profit
        position = 0

    elif action == 0:  # Hold
        reward = 0

    return position, balance, reward

# Train the Q-learning agent
def train_q_learning(df, params):
    q_table = np.zeros((params["n_states"], params["n_actions"]))
    epsilon = params["epsilon"]
    
    for episode in range(50):
        balance = params["initial_balance"]
        position = 0
        entry_price = 0
        total_reward = 0
        
        for step in range(len(df) - 1):
            state = get_state(df.iloc[step], params["state_space"])
            if np.random.rand() < epsilon:
                action = np.random.randint(params["n_actions"])  # Explore
            else:
                action = np.argmax(q_table[state])  # Exploit
            
            next_position, next_balance, reward = take_action(
                action, step, position, balance, entry_price, df)
            next_state = get_state(df.iloc[step + 1], params["state_space"])
            
            best_next_action = np.argmax(q_table[next_state])
            td_target = reward + params["gamma"] * q_table[next_state, best_next_action]
            q_table[state, action] += params["alpha"] * (td_target - q_table[state, action])
            
            position = next_position
            balance = next_balance
            total_reward += reward

        epsilon = max(params["epsilon_min"], epsilon * params["epsilon_decay"])
        logging.info(f"Episode {episode + 1}: Total Reward = {total_reward}, Balance = {balance}, Epsilon = {epsilon}")
    
    return q_table

# Execute trade based on Q-table
def execute_trade(q_table, symbol, amount, state, params):    
    logging.info(f"Latest state for {symbol}: {state} \n\n")
    action = np.argmax(q_table[state])  # Best action based on Q-table
    logging.info(f"Latest Action for {symbol}: {action}->\n\n")

    if action == 1:  # Buy
        logging.info("Executing Buy Order")
        last_price = exchange.fetch_ticker(symbol)['last']
        #order = exchange.create_market_buy_order(symbol, amount)
        stop_loss_price = last_price * (1 - stop_loss_percent)
        take_profit_price = last_price * (1 + take_profit_percent)
        #exchange.create_order(symbol, 'STOP_LOSS_LIMIT', 'sell', amount, stop_loss_price)
        #exchange.create_order(symbol, 'TAKE_PROFIT_LIMIT', 'sell', amount, take_profit_price)

    elif action == 2:  # Sell
        logging.info("Executing Sell Order")
        last_price = exchange.fetch_ticker(symbol)['last']
        #order = exchange.create_market_sell_order(symbol, amount)
        stop_loss_price = last_price * (1 + stop_loss_percent)
        take_profit_price = last_price * (1 - take_profit_percent)
        #exchange.create_order(symbol, 'STOP_LOSS_LIMIT', 'buy', amount, stop_loss_price)
        #exchange.create_order(symbol, 'TAKE_PROFIT_LIMIT', 'buy', amount, take_profit_price)

    else:
        logging.info("No action taken (Hold).")

# Main function
def main():
    params = initialize_parameters()
    df = load_data(symbols[0], timeframe)
    q_table = train_q_learning(df, params)
    
    
    # test trading loop
    for idx,row in df.iterrows():
        #df = load_data(symbols[0], timeframe)  # Fetch latest data
        #state = get_state(df.iloc[-1], params["state_space"])
        state=get_state(row, params["state_space"])
        execute_trade(q_table, symbols[0], trade_amount, state, params)

# Entry point
if __name__ == "__main__":
    main()
