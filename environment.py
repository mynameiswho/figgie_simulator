import logging

import gymnasium as gym
from gymnasium import spaces
from gymnasium.envs.registration import register
from gymnasium.utils.env_checker import check_env
import numpy as np

from game import FiggieGame, Suits, FiggiePlayer

# Register this module as a gym environment. Once registered, the id is usable in gym.make().
register(
    id='figgie-env',                                # call it whatever you want
    entry_point='environment:FiggieEnv', # module_name:class_name
)

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
        # Array 2 = price normalized by dividing by 100
        # Array 3 = buy / sell (as per Side class)
        self.action_space = spaces.Box(
            low=np.array([0, 0, 0, 0]),
            high=np.array([2, 3, 5, 1]),
            dtype=np.float32
        )

        # Gym requires defining the observation space. The observation space consists of the best bids / asks per suit
        self.observation_space = spaces.Dict(
            {
            'best_buys': spaces.Box(0.0, 2.0, shape=(len(Suits),), dtype=np.float32),
            'best_sells': spaces.Box(0.0, 2.0, shape=(len(Suits),), dtype=np.float32),
            }
        )
        
        self.latest_action = 0
        self.latest_obs = 0
        self.player_knocked_out = False


    def _get_obs(self):
        best_buys = []
        best_sells = []
        for suit in Suits:
            bid = self.game.orderbook.best_bid(suit.value)
            ask = self.game.orderbook.best_ask(suit.value)
            best_buys.append(bid[0] if bid else 0.0)
            best_sells.append(ask[0] if ask else 0.0)
        return {
            'best_buys': best_buys,
            'best_sells': best_sells
        }

    # Gym required function (and parameters) to reset the environment
    def reset(self, seed=None, options=None):
        
        # Reset superclass
        super().reset(seed=seed)

        # Reset game, reset player_knocked_out when done
        self.game.reset(self.player_knocked_out)
        self.player_knocked_out = False

        # Construct observation state
        obs = self._get_obs()

        # Additional info to return. For debugging or whatever.
        info = {}

        # Render environment
        if(self.render_mode=='human'):
            self.render()
        
        # Return observation and info
        return obs, info

    # Gym required function (and parameters) to perform an action
    def step(self, action):
        #Initialize
        reward = 0
        terminated = False

        self.latest_action = action

        #Check if game has ended
        reward = 0
        if self.game.game_has_ended():
            logging.info('---GAME HAS ENDED---')
            logging.info(self.game.goal_suit)
            for player in self.game.players:
                logging.info(f'Player {player.player_id} holds {player.get_goal_suit_count(self.game.goal_suit)} of {self.game.goal_suit}')
            final_cash_from_round = self.game.get_final_scores()
            # Assign final cash to players
            for i, player in enumerate(self.game.players):
                player.cash = final_cash_from_round[i]
            logging.info(f'Final scores: {final_cash_from_round}')
            # Reward agent relative to how it placed in the round
            agent_payout = final_cash_from_round[0]
            sorted_payouts = sorted(final_cash_from_round, reverse=True)
            rank = sorted_payouts.index(agent_payout)
            reward = [2, 1.5, 1, 0.5][rank]
            # If any player has final cash < 50, reset all players cash to restart a series of games
            if any(final_cash < 50 for final_cash in final_cash_from_round):
                logging.info('Player knocked, resetting all cash')
                self.player_knocked_out = True
            # If the agent is the one with final cash < 50 assign punishment
            if final_cash_from_round[0] < 50:
                logging.info('Agent knocked, punishing')
                reward = 0
            logging.info(f'Reward to agent: {reward}')
            terminated=True
        else:
            # Agent acts
            self.game.apply_action(0, action)
            self.game.advance_game_one_second()

            # Other players act
            for player in self.players[1:]:
                # Fetch latest game state
                last_obs = self._get_obs()

                # Act and apply
                action = player.act(last_obs)
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
        logging.info(f'Latest agent action: {self.latest_action}')
        logging.info(f'State passed to agent for next action: {self.latest_obs}')
        logging.info(f'Game progress: {self.game.seconds_passed}')

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