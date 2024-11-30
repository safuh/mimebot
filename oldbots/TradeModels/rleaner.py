import numpy as np
import pandas as pd
from stable_baselines3 import DQN
from stable_baselines3.common.vec_env import DummyVecEnv
from gym import spaces
import gym

# Environment state variables
balance = 1000
initial_balance = 1000
position = 0
current_step = 0
df = None

# Define parameters for indicators
sma_short_window = 9
sma_long_window = 21
rsi_period = 14
momentum_period = 10
stochastic_period = 14

# Initialize trading data and indicators
def load_data():
    global df
    df = fetch_data('BTC/USDT', '5m')
    df['SMA_short'] = df['close'].rolling(window=sma_short_window).mean()
    df['SMA_long'] = df['close'].rolling(window=sma_long_window).mean()
    df['RSI'] = calculate_rsi(df, rsi_period)
    df['Momentum'] = df['close'].diff(momentum_period)
    df['Stochastic_RSI'] = calculate_stochastic_rsi(df, stochastic_period)
    df.dropna(inplace=True)
    return df

# Get observation for the current state
def get_observation():
    global current_step, df
    if current_step >= len(df):
        return None
    state = df.iloc[current_step][['close', 'SMA_short', 'SMA_long', 'RSI', 'Momentum', 'Stochastic_RSI']].values
    return state

# Reset environment state
def reset():
    global balance, position, current_step
    balance = initial_balance
    position = 0
    current_step = 0
    return get_observation()

# Step function to take an action, return the next state, reward, and done flag
def step(action):
    global balance, position, current_step
    done = False
    reward = 0

    # Action meanings: 0 = hold, 1 = buy, 2 = sell
    current_price = df.iloc[current_step]['close']
    
    if action == 1:  # Buy
        if position == 0:  # Only buy if no position
            position = 1
            reward -= 1  # Minor cost for entering a trade
        elif position == -1:  # Penalty for conflicting position
            reward -= 10

    elif action == 2:  # Sell
        if position == 1:  # Close long position
            profit = current_price - entry_price
            reward += profit  # Reward based on profit
            position = 0
        elif position == -1:  # Close short position
            profit = entry_price - current_price
            reward += profit
            position = 0

    current_step += 1
    if current_step >= len(df) - 1:
        done = True

    next_state = get_observation()
    return next_state, reward, done, {}

# Functional wrapper to create custom environment
def make_env():
    global df
    load_data()
    
    # Gym-compatible functional environment definition
    env = gym.Env()
    
    # Define action and observation space
    env.action_space = spaces.Discrete(3)  # [hold, buy, sell]
    env.observation_space = spaces.Box(low=0, high=1, shape=(6,), dtype=np.float32)
    
    # Set reset and step functions
    env.reset = reset
    env.step = step

    return DummyVecEnv([lambda: env])

# Train the RL model
env = make_env()
model = DQN("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=10000)

# Run the model in simulation
obs = reset()
for _ in range(len(df) - 1):
    action, _ = model.predict(obs)
    obs, reward, done, _ = step(action)
    if done:
        break
