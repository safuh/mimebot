import gym
import numpy as np
import pandas as pd
from stable_baselines3 import DQN
from stable_baselines3.common.envs import DummyVecEnv
from gym import spaces

# Custom Trading Environment
class TradingEnv(gym.Env):
    def __init__(self, df, initial_balance=1000):
        super(TradingEnv, self).__init__()
        self.df = df
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.position = 0  # 1 for long, -1 for short
        self.current_step = 0

        # Define action and observation space
        self.action_space = spaces.Discrete(3)  # [hold, buy, sell]
        self.observation_space = spaces.Box(low=0, high=1, shape=(6,), dtype=np.float32)

    def reset(self):
        self.balance = self.initial_balance
        self.position = 0
        self.current_step = 0
        return self._get_obs()

    def _get_obs(self):
        state = self.df.iloc[self.current_step][['close', 'SMA_short', 'SMA_long', 'RSI', 'Momentum', 'Stochastic_RSI']].values
        return state

    def step(self, action):
        done = False
        reward = 0

        # Action meanings: 0 = hold, 1 = buy, 2 = sell
        current_price = self.df.iloc[self.current_step]['close']
        
        if action == 1:  # Buy
            if self.position == 0:
                self.position = 1
                reward -= 1  # Minor cost for entering a trade
            elif self.position == -1:
                reward -= 10  # Penalty for conflicting position
        
        elif action == 2:  # Sell
            if self.position == 1:
                profit = current_price - self.entry_price
                reward += profit  # Reward based on profit
                self.position = 0
            elif self.position == -1:
                profit = self.entry_price - current_price
                reward += profit
                self.position = 0
        
        self.current_step += 1
        if self.current_step >= len(self.df) - 1:
            done = True

        return self._get_obs(), reward, done, {}

# Load data and train the model
df = fetch_data('BTC/USDT', '5m')
env = DummyVecEnv([lambda: TradingEnv(df)])
dqn_model = DQN("MlpPolicy", env, verbose=1)
dqn_model.learn(total_timesteps=10000)

# Make predictions (simulation)
obs = env.reset()
for _ in range(len(df) - 1):
    action, _ = dqn_model.predict(obs)
    obs, reward, done, info = env.step(action)
    if done:
        break
