from collections import Counter
from matplotlib import pyplot as plt

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from environment import FiggieEnv, action_log
import logging

logging.basicConfig(
    filename='figgie.log',          # Log file name
    level=logging.INFO,             # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s'
)

dummyenv = DummyVecEnv([lambda: FiggieEnv('human')])
vecenv = VecNormalize(dummyenv, norm_reward=False)

model = PPO("MultiInputPolicy", vecenv, verbose=1)
model.learn(total_timesteps=100000)
model.save("figgie_agent")


def plot_actions():
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    # Plot Action distribution
    ax = axes[0][0]
    counts = Counter([a.name for a in action_log['action']])

    ax.bar(counts.keys(), counts.values())
    ax.set_ylabel("Count")
    ax.set_title("Action Distribution")

    # Plot Suit distribution
    ax = axes[0][1]
    counts = Counter([a.name for a in action_log['suit']])

    ax.bar(counts.keys(), counts.values())
    ax.set_ylabel("Count")
    ax.set_title("Suit Distribution")

    # Plot Side distribution
    ax = axes[1][0]

    counts = Counter([a.name for a in action_log['side']])

    ax.bar(counts.keys(), counts.values())
    ax.set_ylabel("Count")
    ax.set_title("Side Distribution")

    # Plot Prices
    ax = axes[1][1]
    
    bin_counts, bin_edges = np.histogram(action_log['price'], bins=100, range=(0.0, 150))

    # Bar plot
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    ax.bar(bin_centers, bin_counts, width=0.15)
    ax.set_ylabel("Count")
    ax.set_title("Price Histogram")
    
    plt.show()


plot_actions()