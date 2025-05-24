import logging

import gymnasium as gym
from gymnasium import spaces
from gymnasium.envs.registration import register
from gymnasium.utils.env_checker import check_env
import numpy as np

from game import FiggieGame, FiggieSide, FiggiePlayer
from enums import *

# Register this module as a gym environment. Once registered, the id is usable in gym.make().
register(
    id='figgie-env',                                # call it whatever you want
    entry_point='environment:FiggieEnv', # module_name:class_name
)

action_log = {
    'action': [],
    'suit': [],
    'price': [],
    'side': []
}

# Implement our own gym env, must inherit from gym.Env
# https://gymnasium.farama.org/api/env/
class FiggieEnv(gym.Env):
    # metadata is a required attribute
    # render_modes in our environment is either None or 'human'.
    # render_fps is not used in our env, but we are require to declare a non-zero value.
    metadata = {"render_modes": ["human"], 'render_fps': 1}

    def __init__(self, render_mode=None):
        
        self.render_mode = render_mode

        # Initialize the Figgie problem
        self.players = [FiggiePlayer(0), FiggiePlayer(1), FiggiePlayer(2), FiggiePlayer(3)]
        self.game = FiggieGame(self.players)

        # Gym requires defining the action space. The action space is player's set of possible actions.
        # Training code can call action_space.sample() to randomly select an action.
        # Array 0 = action (as per Actions class)
        # Array 1 = suit (as per Suits class)
        # Array 2 = price
        # Array 3 = buy / sell (as per Side class)

        self.action_space = spaces.MultiDiscrete([3, 4, 150, 2])

        # Gym requires defining the observation space. The observation space consists of the best bids / asks per suit
        self.observation_space = spaces.Dict(
            {
            'best_buys': spaces.MultiDiscrete([150, 150, 150, 150]),
            'best_sells': spaces.MultiDiscrete([150, 150, 150, 150]),
            'own_cards': spaces.MultiDiscrete([12, 12, 12, 12]),
            'own_cash': spaces.Discrete(1200),
            'time_left': spaces.Discrete(241),
            }
        )
        
        self.latest_action = 0
        self.latest_obs = 0
        self.player_knocked_out = False
        self.player_start_cash = 0

    def _get_obs(self):
        best_buys = []
        best_sells = []
        agent_hand = []
        for suit in FiggieSuit:
            bid = self.game.orderbook.best_bid(suit)
            ask = self.game.orderbook.best_ask(suit)
            best_buys.append(bid[0] if bid else 0.0)
            best_sells.append(ask[0] if ask else 0.0)
            agent_hand.append(self.game.players[0].get_suit_count(suit))
        return {
            'best_buys': np.array(best_buys),
            'best_sells': np.array(best_sells),
            'own_cards': np.array(agent_hand),
            'own_cash': self.game.players[0].cash,
            'time_left': self.game.seconds_passed
        }

    # Gym required function (and parameters) to reset the environment
    def reset(self, seed=None, options=None):
        # Reset superclass
        super().reset(seed=seed)
        # Reset game, reset player_knocked_out when done
        self.game.reset(self.player_knocked_out)
        self.player_knocked_out = False
        # Construct observation state
        self.latest_obs = self._get_obs()
        # Reset action state
        self.latest_action = 0
        # Set AI agent start cash to calculate reward at end of round
        self.player_start_cash = self.game.players[0].cash
        # Additional info to return. For debugging or whatever.
        info = {}
        # Render environment
        if(self.render_mode=='human'):
            self.render()
        # Return observation and info
        return self.latest_obs, info

    # Gym required function (and parameters) to perform an action
    def step(self, action):
        #Initialize
        terminated = False
        converted_action = FiggieAction(
            FiggieInGameAction(action[0]),
            FiggieSuit(action[1]),
            FiggieSide(action[3]),
            action[2]
            )
        self.latest_action = converted_action
        self._log_agent_action(converted_action)
        #Check if game has ended
        reward = 0
        if self.game.game_has_ended():
            logging.info('---GAME HAS ENDED---')
            for player in self.game.players:
                logging.info(f'Player {player.player_id} holds {player.get_suit_count(self.game.goal_suit)} of {self.game.goal_suit}')
            final_cash_from_round = self.game.get_final_scores()
            # Assign final cash to players
            for i, player in enumerate(self.game.players):
                player.cash = final_cash_from_round[i]
            logging.info(f'Final scores: {final_cash_from_round}')
            # Reward agent relative to how it placed in the round
            agent_payout = final_cash_from_round[0]
            reward = agent_payout - self.player_start_cash
            # If any player has final cash < 50, reset all players cash to restart a series of games
            if any(final_cash < 50 for final_cash in final_cash_from_round):
                logging.info('Player knocked, resetting all cash')
                self.player_knocked_out = True
            # If the agent is the one with final cash < 50 assign punishment
            if agent_payout < 50:
                logging.info('Agent knocked, punishing')
                reward = -1000
            logging.info(f'Reward to agent: {reward}')
            terminated=True
        else:
            # Agent acts
            self.game.apply_action(0, converted_action)
            # Other players act
            for player in self.players[1:]:
                # Fetch latest game state
                last_obs = self._get_obs()
                # Act and apply
                action = player.generate_action(last_obs)
                self.game.apply_action(player.player_id, action)
            self.game.advance_game_one_second()
            # Construct observation state for agent's next round
            self.latest_obs = self._get_obs()
        # Render environment
        if(self.render_mode=='human'):
            self.render()
            
        # Return observation, reward, terminated, truncated, info (for debugging/other purposes)
        return self.latest_obs, reward, terminated, False, {}

    # Gym required function to render environment
    def render(self):
        logging.debug(f'Latest agent action: {self.latest_action}')
        logging.debug(f'State passed to agent for next action: {self.latest_obs}')

    def _log_agent_action(self, action: FiggieAction):
        action_log['action'].append(action.action)
        action_log['suit'].append(action.suit)
        action_log['price'].append(action.price)
        action_log['side'].append(action.acting_intent_side)

'''
# For unit testing
if __name__=="__main__":
    env = gym.make('figgie-env', render_mode='human')

    # Use this to check our custom environment
    print("Check environment begin")
    check_env(env.unwrapped)
    print("Check environment end")

    # Reset environment
    obs = env.reset()[0]

    # Take some random actions
    rand_action = env.action_space.sample()
    print(rand_action)
    print(env.step(rand_action))
'''