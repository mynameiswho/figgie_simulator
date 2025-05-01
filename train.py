from stable_baselines3 import PPO
from environment import FiggieEnv

env = FiggieEnv('human')

model = PPO("MultiInputPolicy", env, verbose=1)
model.learn(total_timesteps=5000)
model.save("figgie_agent")
