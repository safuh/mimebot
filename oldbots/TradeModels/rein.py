import numpy as np
import pandas as pd
import logging
from fetch_ohlcv import exchange, fetch_data  # type: ignore
from indicators import calculate_indicators  # type: ignore
from constants import *  # Ensure constants like `stop_loss_percent` and `take_profit_percent` are defined

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

# Execute trade based on action
def execute_trade(action, symbol, amount, balance, entry_price, stop_loss_percent, take_profit_percent, current_price):
    reward = 0
    position = 0

    if action == 1:  # Buy
        entry_price = current_price
        position = 1
        reward = -1  # Small penalty for initiating a trade

    elif action == 2:  # Sell
        if position == 1:
            profit = current_price - entry_price
            if profit >= entry_price * take_profit_percent:
                reward = profit  # Reward for reaching take-profit
            elif profit <= entry_price * -stop_loss_percent:
                reward = -entry_price * stop_loss_percent  # Penalty for hitting stop-loss
            else:
                reward = profit  # Profit-based reward
            balance += profit
        position = 0

    return position, balance, reward

# Train the Q-learning agent
def train_q_learning(df, params, symbol, stop_loss_percent, take_profit_percent):
    q_table = np.zeros((params["n_states"], params["n_actions"]))
    epsilon = params["epsilon"]

    for episode in range(50):  # Training episodes
        balance = params["initial_balance"]
        position = 0
        entry_price = 0
        total_reward = 0

        for step in range(len(df) - 1):
            current_price = df.iloc[step]['close']
            state = get_state(df.iloc[step], params["state_space"])
            
            # Exploration or exploitation
            if np.random.rand() < epsilon:
                action = np.random.randint(params["n_actions"])  # Explore
            else:
                action = np.argmax(q_table[state])  # Exploit
            
            # Execute action and update Q-table
            next_position, next_balance, reward = execute_trade(
                action, symbol, trade_amount, balance, entry_price, stop_loss_percent, take_profit_percent, current_price
            )
            next_state = get_state(df.iloc[step + 1], params["state_space"])
            best_next_action = np.argmax(q_table[next_state])
            
            td_target = reward + params["gamma"] * q_table[next_state, best_next_action]
            q_table[state, action] += params["alpha"] * (td_target - q_table[state, action])
            
            # Update variables for next step
            position = next_position
            balance = next_balance
            total_reward += reward

        # Decay epsilon
        epsilon = max(params["epsilon_min"], epsilon * params["epsilon_decay"])
        logging.info(f"Episode {episode + 1}: Total Reward = {total_reward}, Balance = {balance}, Epsilon = {epsilon}")

    return q_table

# Test the agent
def test_agent(df, q_table, params, symbol, stop_loss_percent, take_profit_percent):
    balance = params["initial_balance"]
    position = 0
    entry_price = 0

    for step in range(len(df) - 1):
        current_price = df.iloc[step]['close']
        state = get_state(df.iloc[step], params["state_space"])
        action = np.argmax(q_table[state])

        position, balance, reward = execute_trade(
            action, symbol, trade_amount, balance, entry_price, stop_loss_percent, take_profit_percent, current_price
        )
        logging.info(f"Step {step + 1}: Action = {action}, Reward = {reward}, Balance = {balance}")

# Main function
def main():
    params = initialize_parameters()
    df = load_data(symbols[0], timeframe)

    stop_loss_percent = 0.02  # 2% stop-loss
    take_profit_percent = 0.05  # 5% take-profit

    q_table = train_q_learning(df, params, symbols[0], stop_loss_percent, take_profit_percent)
    test_agent(df, q_table, params, symbols[0], stop_loss_percent, take_profit_percent)

# Entry point
if __name__ == "__main__":
    main()
