import random
from typing import List
import logging

from orderbook import SuitOrderBook
from enums import *


class FiggiePlayer:
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.hand = []
        self.cash = 350
    
    def reset(self, any_player_knocked_out: bool):
        self.hand = []
        if any_player_knocked_out:
            self.cash = 350
    
    def generate_action(self, offers: dict) -> FiggieAction:
        # Bots act as follows: pick a suit at random, pick a side at random
        best_buys = offers['best_buys']
        best_sells = offers['best_sells']
        suit = random.choice(list(FiggieSuit))
        side = random.choice(list(FiggieSide))
        action = FiggieAction(FiggieInGameAction.PASS, None, None, None)
        if side == FiggieSide.BUY:
            best_buy = best_buys[suit.value]
            if best_buy == 0 and self.cash >= 10:
                # If the side does not contain a quote and is buy and bot has enough cash -> place random quote between 0 and 10
                action = FiggieAction(FiggieInGameAction.SHOW, suit, side, random.randint(0, 10))
            # If someone offers to buy at a high price then sell to them
            elif best_buy >= 7 and suit in self.hand:
                # If the side is buy and contains a bid >= 7 and the bot has the correct card -> sell
                action = FiggieAction(FiggieInGameAction.TAKE, suit, FiggieSide.SELL, 0)
        elif side == FiggieSide.SELL:
            best_sell = best_sells[suit.value]
            if best_sell == 0 and suit in self.hand:
                # If the side does not contain a quote and is sell and the bot has the suit -> place random quote between 10 and 20
                action = FiggieAction(FiggieInGameAction.SHOW, suit, side, random.randint(10, 20))
            # If someone offers to sell at a low price then buy from them
            elif best_sell <= 13 and self.cash >= 13:
                # If the side is sell and contains an ask < 13 -> buy
                action = FiggieAction(FiggieInGameAction.TAKE, suit, FiggieSide.BUY, 0)
        return action

    def add_cash(self, cash_to_add: int):
        self.cash += cash_to_add

    def subtract_cash(self, cash_to_subtract: int):
        self.cash -= cash_to_subtract

    def receive_card(self, card: FiggieSuit):
        self.hand.append(card)

    def remove_card(self, card_index: int):
        for card in self.hand:
            if card[1] == card_index:
                self.hand.remove(card)
                return card
        return None

    def get_suit_count(self, suit: FiggieSuit) -> int:
        suit_cnt = 0
        for card in self.hand:
            if card == suit:
                suit_cnt += 1
        return suit_cnt


class FiggieGame:
    def __init__(self, players: List[FiggiePlayer]):
        self.players = players

    def _build_deck(self) -> list:
        deck = []
        goal_suit_cards = random.choice([8, 10])
        deck.extend([self.goal_suit] * goal_suit_cards)
        if self.goal_suit in [FiggieSuit.DIAMONDS, FiggieSuit.HEARTS]:
            deck.extend([FiggieSuit.CLUBS] * 10)
            deck.extend([FiggieSuit.SPADES] * 10)
            if self.goal_suit == FiggieSuit.HEARTS:
                deck.extend([FiggieSuit.DIAMONDS] * 12)
            else:
                deck.extend([FiggieSuit.HEARTS] * 12)
        elif self.goal_suit in [FiggieSuit.CLUBS, FiggieSuit.SPADES]:
            deck.extend([FiggieSuit.DIAMONDS] * 10)
            deck.extend([FiggieSuit.HEARTS] * 10)
            if self.goal_suit == FiggieSuit.CLUBS:
                deck.extend([FiggieSuit.SPADES] * 12)
            else:
                deck.extend([FiggieSuit.CLUBS] * 12)
        return deck

    def _deal_cards(self):
        random.shuffle(self.deck)
        for i, card in enumerate(self.deck):
            self.players[i % len(self.players)].receive_card(card)

    def reset(self, player_knocked_out: bool):
        for player in self.players:
            player.reset(player_knocked_out)
        [player.subtract_cash(50) for player in self.players]
        self.goal_suit = random.choice(list(FiggieSuit))
        self.pot = 50 * len(self.players)
        self.seconds_passed = 0
        self.orderbook = SuitOrderBook(list(FiggieSuit))
        self.deck = self._build_deck()
        self._deal_cards()
        logging.info('---GAME RESET---')
        logging.info('Starting state')
        for player in self.players:
            logging.info(f'Player {player.player_id} has cash {player.cash}')
        logging.info(f'Goal suit {self.goal_suit}')

    def advance_game_one_second(self):
        self.seconds_passed += 1
    
    def apply_action(self, player_id: int, figgie_action: FiggieAction):
        if figgie_action.action == FiggieInGameAction.PASS:
            return
        elif figgie_action.action == FiggieInGameAction.SHOW:
            self.orderbook.post_order(player_id, figgie_action.suit, figgie_action.price, figgie_action.acting_intent_side)
        elif figgie_action.action == FiggieInGameAction.TAKE:
            # If player_intent_side == BUY -> we must accept best price on the SELL side, likewise on opposite side
            if figgie_action.acting_intent_side == FiggieSide.BUY:
                self.accept_best_price(player_id, figgie_action.suit, FiggieSide.SELL)
            else:
                self.accept_best_price(player_id, figgie_action.suit, FiggieSide.BUY)
        
    def accept_best_price(self, aggressor_id: int, suit: FiggieSuit, best_price_side: FiggieSide):
        # If best_price_side = BUY -> aggressor 
        best_order = self.orderbook.best(best_price_side, suit)
        price = best_order[0]
        counterpart_id = best_order[1]
        # Do not allow trading with oneself or accept non-existing order
        if counterpart_id == -1 or counterpart_id == aggressor_id:
            return
        aggressor = self.players[aggressor_id]
        counterpart = self.players[counterpart_id]
        # Counterpart is seller
        if best_price_side == FiggieSide.SELL:
            # Counterpart must hold the card to trade AND aggressor must have enough cash
            if suit in counterpart.hand and aggressor.cash >= price:
                counterpart.hand.remove(suit)
                aggressor.hand.append(suit)
                aggressor.cash -= price
                counterpart.cash += price
                logging.info(f'Player {counterpart_id} sells to Player {aggressor_id} {suit} @ {price}')
        # Counterpart is buyer
        elif best_price_side == FiggieSide.BUY:
            # Aggressor must hold the card to trade AND counterpart must have enough cash
            if suit in aggressor.hand and counterpart.cash >= price:
                aggressor.hand.remove(suit)
                counterpart.hand.append(suit)
                aggressor.cash += price
                counterpart.cash -= price
                logging.info(f'Player {counterpart_id} buys from Player {aggressor_id} {suit} @ {price}')
        self.orderbook.reset()
        return True

    def game_has_ended(self) -> bool:
        if self.seconds_passed >= 4 * 60:
            return True
        return False

    def get_final_scores(self):
        counts = [p.get_suit_count(self.goal_suit) for p in self.players]
        payouts = [0, 0, 0, 0]
        #Standard payout
        payouts[0] += 10 * counts[0]
        payouts[1] += 10 * counts[1]
        payouts[2] += 10 * counts[2]
        payouts[3] += 10 * counts[3]
        self.pot -= sum(payouts)
        #Bonus
        max_val = max(counts)
        winners = [i for i, val in enumerate(counts) if val == max_val]
        number_of_winners = len(winners)
        for w in winners:
            payouts[w] += self.pot/number_of_winners
        final_cash = [player.cash for player in self.players]
        return [x + y for x,y in zip(payouts, final_cash)]


if __name__ == '__main__':
    players = [FiggiePlayer(0), FiggiePlayer(1), FiggiePlayer(2), FiggiePlayer(3)]
    game = FiggieGame(players)
    game.reset(False)
    while not game.game_has_ended():
        player = random.choice(players)
        best_buys = []
        best_sells = []
        for suit in FiggieSuit:
            best_buys.append(game.orderbook.best_bid(suit)[0])
            best_sells.append(game.orderbook.best_ask(suit)[0])
        action = player.generate_action({'best_buys': best_buys, 'best_sells': best_sells})
        game.apply_action(player.player_id, action)
        game.advance_game_one_second()
    print(game.goal_suit)
    for player in players:
        print(f'Player {player.player_id} holds {player.get_suit_count(game.goal_suit)} of {game.goal_suit}')
    print(game.get_final_scores())
    a = 1
