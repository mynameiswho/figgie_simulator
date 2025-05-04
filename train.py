from stable_baselines3 import PPO
from environment import FiggieEnv
import logging

logging.basicConfig(
    filename='figgie.log',          # Log file name
    level=logging.INFO,             # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s'
)

env = FiggieEnv('human')

model = PPO("MultiInputPolicy", env, verbose=1)
model.learn(total_timesteps=100000)
model.save("figgie_agent")
