from stable_baselines3 import PPO
from game import MultiRoundPokerEnv, hand_strength_bot

env = MultiRoundPokerEnv(hand_strength_bot)
model = PPO.load("poker_agent")

wins, losses = 0, 0

for episode in range(20):
    obs = env.reset()
    done = False
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, _ = env.step(action)

    env.render()
    print(f"Reward: {reward}\n")
    if reward > 0:
        wins += 1
    else:
        losses += 1

print(f"\nFinal score: {wins} wins / {losses} losses")
