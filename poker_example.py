import gym
from gym import spaces
import numpy as np
import random


class PokerPlayer:
    def __init__(self, name, policy_fn):
        self.name = name
        self.hand_strength = 0.0
        self.folded = False
        self.chips = 100
        self.bet = 0
        self.policy_fn = policy_fn  # function(state) -> action

    def reset(self):
        self.hand_strength = random.random()
        self.folded = False
        self.bet = 0

    def act(self, observation):
        return self.policy_fn(observation)


class MultiRoundPokerEnv(gym.Env):
    def __init__(self, opponent_policy_fn):
        super().__init__()

        self.action_space = spaces.Discrete(3)  # 0 = fold, 1 = call, 2 = raise
        self.observation_space = spaces.Box(low=0, high=1, shape=(3,), dtype=np.float32)  # [hand_strength, pot, last_opponent_action]

        self.agent = PokerPlayer("Agent", policy_fn=None)  # Policy set externally
        self.opponent = PokerPlayer("Opponent", policy_fn=opponent_policy_fn)

        self.pot = 0
        self.current_round = 0
        self.max_rounds = 2  # Can be 4 for full poker: preflop, flop, turn, river
        self.last_opponent_action = 1  # Assume call

    def reset(self):
        self.agent.reset()
        self.opponent.reset()
        self.pot = 0
        self.current_round = 0
        self.last_opponent_action = 1
        self.done = False
        return self._get_obs()

    def _get_obs(self):
        return np.array([
            self.agent.hand_strength,
            self.pot / 100,  # Normalize pot
            self.last_opponent_action / 2  # Normalize action (0-2)
        ], dtype=np.float32)

    def step(self, action):
        if self.done:
            raise Exception("Episode is done. Call reset()")

        # Agent action
        agent_action = action
        if agent_action == 0:
            self.agent.folded = True
            reward = -1
            self.done = True
            return self._get_obs(), reward, self.done, {}

        self.agent.bet += 1 if agent_action == 1 else 2
        self.pot += self.agent.bet

        # Opponent action
        opponent_obs = np.array([
            self.opponent.hand_strength,
            self.pot / 100,
            agent_action / 2
        ], dtype=np.float32)

        opponent_action = self.opponent.act(opponent_obs)
        self.last_opponent_action = opponent_action

        if opponent_action == 0:
            self.opponent.folded = True
            reward = 1
            self.done = True
            return self._get_obs(), reward, self.done, {}

        self.opponent.bet += 1 if opponent_action == 1 else 2
        self.pot += self.opponent.bet

        self.current_round += 1

        if self.current_round >= self.max_rounds:
            self.done = True
            if self.agent.hand_strength > self.opponent.hand_strength:
                reward = 1
            elif self.agent.hand_strength < self.opponent.hand_strength:
                reward = -1
            else:
                reward = 0
        else:
            reward = 0

        return self._get_obs(), reward, self.done, {}

    def render(self, mode='human'):
        print(f"Round {self.current_round}")
        print(f"Agent hand: {self.agent.hand_strength:.2f}")
        print(f"Opponent hand: {self.opponent.hand_strength:.2f}")
        print(f"Pot: {self.pot}")
        print(f"Last opponent action: {self.last_opponent_action}")
