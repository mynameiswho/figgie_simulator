from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from environment import FiggieEnv
import logging

logging.basicConfig(
    filename='figgie.log',          # Log file name
    level=logging.INFO,             # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s'
)

dummyenv = DummyVecEnv([lambda: FiggieEnv('human')])
vecenv = VecNormalize(dummyenv, norm_reward=False)

model = PPO("MultiInputPolicy", vecenv, verbose=1)
model.learn(total_timesteps=1_000_000)
model.save("figgie_agent")
