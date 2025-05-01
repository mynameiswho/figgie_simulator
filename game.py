import random
from typing import List

from orderbook import SuitOrderBook
from enums import *


class FiggiePlayer:
    def __init__(self, player_id: int):
        self.player_id = player_id
        self.hand = []
        self.cash = 350
    
    def reset(self):
        self.hand = []
        self.cash = 350
    
    def act(self, offers: dict):
        # The bots act as follows: pick a suit at random, pick a side at random
        best_buys = offers['best_buys']
        best_sells = offers['best_sells']
        suit = random.choice(list(Suits))
        side = random.choice(list(Side))
        if side == Side.BUY:
            best_buy = best_buys[suit.value] * 100
            if best_buy == 0 and self.cash >= 10:
                # If the side does not contain a quote and is buy and bot has enough cash -> place random quote between 0 and 10
                return FiggieActions.SHOW.value, suit.value, random.randint(0, 10)/100, side.value
            elif best_buy >= 7 and suit in self.hand:
                # If the side is buy and contains a bid >= 7 and the bot has the correct card -> sell
                return FiggieActions.TAKE.value, suit.value, 0, side.value
        elif side == Side.SELL:
            best_sell = best_sells[suit.value] * 100
            if best_sell == 0 and suit in self.hand:
                # If the side does not contain a quote and is sell and the bot has the suit -> place random quote between 10 and 20
                return FiggieActions.SHOW.value, suit.value, random.randint(10, 20)/100, side.value
            elif best_sell <= 13 and self.cash >= 13:
                # If the side is sell and contains an ask < 13 -> buy
                return FiggieActions.TAKE.value, suit.value, 0, side.value
        return FiggieActions.PASS.value, None, None, None

    def add_cash(self, cash_to_add: int):
        self.cash += cash_to_add

    def subtract_cash(self, cash_to_subtract: int):
        self.cash -= cash_to_subtract

    def receive_card(self, card):
        self.hand.append(card)

    def remove_card(self, card_index):
        for card in self.hand:
            if card[1] == card_index:
                self.hand.remove(card)
                return card
        return None

    def get_goal_suit_count(self, goal_suit: Suits) -> int:
        goal_cnt = 0
        for card in self.hand:
            if card == goal_suit:
                goal_cnt += 1
        return goal_cnt


class FiggieGame:
    def __init__(self, players: List[FiggiePlayer]):
        self.players = players
        self.reset()

    def _build_deck(self) -> list:
        deck = []
        goal_suit_cards = random.choice([8, 10])
        deck.extend([self.goal_suit] * goal_suit_cards)
        if self.goal_suit in [Suits.DIAMONDS, Suits.HEARTS]:
            deck.extend([Suits.CLUBS] * 10)
            deck.extend([Suits.SPADES] * 10)
            if self.goal_suit == Suits.HEARTS:
                deck.extend([Suits.DIAMONDS] * 12)
            else:
                deck.extend([Suits.HEARTS] * 12)
        elif self.goal_suit in [Suits.CLUBS, Suits.SPADES]:
            deck.extend([Suits.DIAMONDS] * 10)
            deck.extend([Suits.HEARTS] * 10)
            if self.goal_suit == Suits.CLUBS:
                deck.extend([Suits.SPADES] * 12)
            else:
                deck.extend([Suits.CLUBS] * 12)
        return deck

    def _deal_cards(self):
        random.shuffle(self.deck)
        for i, card in enumerate(self.deck):
            self.players[i % len(self.players)].receive_card(card)

    def reset(self):
        for player in self.players:
            player.reset()
        [player.subtract_cash(50) for player in self.players]
        self.goal_suit = random.choice(list(Suits))
        self.pot = 200
        self.seconds_passed = 0
        self.orderbook = SuitOrderBook(list(Suits))
        self.deck = self._build_deck()
        self._deal_cards()

    def advance_game_one_second(self):
        self.seconds_passed += 1
    
    def apply_action(self, player_id: int, action: tuple):
        act = int(action[0])
        if act == FiggieActions.PASS.value:
            return
        suit = int(action[1])
        price = action[2]
        side = int(action[3])
        if act == FiggieActions.SHOW.value:
            self.orderbook.post_order(player_id, suit, price, side)
        elif act == FiggieActions.TAKE.value:
            self.accept_offer(player_id, suit, Side(side))
        
    def accept_offer(self, accepting_id: int, suit: Suits, side: Side):
        offer = self.orderbook.best(side, suit)
        price = offer[0] * 100
        seller_id = offer[1]
        # Handle accepting a non-existing price or trying to trade with oneself
        if seller_id == -1 or seller_id == accepting_id:
            return
        buyer = self.players[accepting_id]
        seller = self.players[seller_id]
        # Handle the case where the seller no longer holds the card to trade due to having taken another player's Buy order in the same card and buyer has enough cash
        if Suits(suit) in seller.hand and buyer.cash >= price:
            seller.hand.remove(Suits(suit))
            buyer.hand.append(Suits(suit))
            buyer.cash -= price
            seller.cash += price
            if side == Side.BUY:
                print(f'Player {accepting_id} sells to Player {seller_id} {Suits(suit)} @ {price}')
            else:
                print(f'Player {accepting_id} buys from Player {seller_id} {Suits(suit)} @ {price}')
            self.orderbook.reset()
        return True

    def game_has_ended(self) -> bool:
        if self.seconds_passed >= 4 * 60:
            return True
        return False

    def get_final_scores(self):
        counts = [p.get_goal_suit_count(self.goal_suit) for p in self.players]
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


'''
if __name__ == '__main__':
    players = [FiggiePlayer(0), FiggiePlayer(1), FiggiePlayer(2), FiggiePlayer(3)]
    game = FiggieGame(players)
    while not game.game_has_ended():
        player = random.choice(players)
        best_buys = []
        best_sells = []
        for suit in Suits:
            best_buys.append(game.orderbook.best_bid(suit.value)[0])
            best_sells.append(game.orderbook.best_ask(suit.value)[0])
        action = player.act({'best_buys': best_buys, 'best_sells': best_sells})
        game.apply_action(player.player_id, action)
        game.advance_game_one_second()
    print(game.goal_suit)
    for player in players:
        print(f'Player {player.player_id} holds {player.get_goal_suit_count(game.goal_suit)} of {game.goal_suit}')
    print(game.get_final_scores())
    a = 1
'''