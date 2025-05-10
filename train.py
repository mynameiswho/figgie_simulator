from collections import Counter
from matplotlib import pyplot as plt

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.callbacks import EvalCallback
from environment import FiggieEnv, action_log
import logging

logging.basicConfig(
    filename='./logs/figgie.log',          # Log file name
    level=logging.INFO,             # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s'
)

dummyenv = DummyVecEnv([lambda: FiggieEnv('human')])
vecenv = VecNormalize(dummyenv)
vecenv.save('./output/vecnormal.pkl')

dummy_eval_env = DummyVecEnv([lambda: FiggieEnv('human')])
eval_env = VecNormalize.load('./output/vecnormal.pkl', dummy_eval_env)

eval_callback = EvalCallback(
    eval_env,
    best_model_save_path="./logs/best_model/",
    log_path="./logs/results/",
    eval_freq=50_000,
    n_eval_episodes=10,
    deterministic=True,
    render=False
)

model = PPO("MultiInputPolicy", vecenv, verbose=1)
model.learn(total_timesteps=500_000, callback=eval_callback)
model.save("figgie_agent")

# Load evaluation results
data = np.load("./logs/results/evaluations.npz")

# Data contents:
timesteps = data["timesteps"]       # when each evaluation happened
results = data["results"]           # mean reward per evaluation
ep_lengths = data["ep_lengths"]     # episode lengths per evaluation (optional)

mean_rewards = results.mean(axis=1)

plt.figure(figsize=(8, 5))
plt.plot(timesteps, mean_rewards, marker='o')
plt.xlabel("Timesteps")
plt.ylabel("Mean Evaluation Reward")
plt.title("Agent Evaluation Rewards Over Time")
plt.grid(True)
plt.tight_layout()

'''
def plot_actions(actions: list, suits: list, sides: list, prices: list):
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    # Plot Action distribution
    ax = axes[0][0]
    counts = Counter([a.name for a in actions])

    ax.bar(counts.keys(), counts.values())
    ax.set_ylabel("Count")
    ax.set_title("Action Distribution")

    # Plot Suit distribution
    ax = axes[0][1]
    counts = Counter([a.name for a in suits])

    ax.bar(counts.keys(), counts.values())
    ax.set_ylabel("Count")
    ax.set_title("Suit Distribution")

    # Plot Side distribution
    ax = axes[1][0]

    counts = Counter([a.name for a in sides])

    ax.bar(counts.keys(), counts.values())
    ax.set_ylabel("Count")
    ax.set_title("Side Distribution")

    # Plot Prices
    ax = axes[1][1]
    
    bin_counts, bin_edges = np.histogram(prices, bins=15, range=(0.0, 150))

    # Bar plot
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    ax.bar(bin_centers, bin_counts, width=0.15)
    ax.set_ylabel("Count")
    ax.set_title("Price Histogram")

# All actions
plot_actions(action_log['action'], action_log['suit'], action_log['side'], action_log['price'])

# Last 1000 actions
plot_actions(action_log['action'][-1000:], action_log['suit'][-1000:], action_log['side'][-1000:], action_log['price'][-1000:])
'''

plt.show()