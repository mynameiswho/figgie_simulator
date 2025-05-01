import heapq
import itertools
from typing import List

from enums import *


class OrderBook:
    def __init__(self):
        self.bids = []  # max-heap: (-price, order)
        self.asks = []  # min-heap: (price, order)
        self.counter = itertools.count()

    def post_order(self, side, price, player_id):
        arrival_id = next(self.counter)
        order = (price, player_id)
        if side == Side.BUY.value:
            heapq.heappush(self.bids, (-price, arrival_id, order))
        else:  # 'sell'
            heapq.heappush(self.asks, (price, arrival_id, order))

    def best_bid(self):
        return self.bids[0][2] if self.bids else (0, -1)

    def best_ask(self):
        return self.asks[0][2] if self.asks else (0, -1)

    def pop_best_bid(self):
        return heapq.heappop(self.bids)[2] if self.bids else (0, -1)

    def pop_best_ask(self):
        return heapq.heappop(self.asks)[2] if self.asks else (0, -1)

    def __str__(self):
        return f"Bids: {[(-p, o) for p, id, o in self.bids]}\\nAsks: {self.asks}"


class SuitOrderBook:
    def __init__(self, suits: List[Suits]):
        self.suits = suits
        self.reset()
    
    def reset(self):
        self.books = {suit.value: OrderBook() for suit in self.suits}

    def post_order(self, player_id, suit, price, side):
        self.books[suit].post_order(side, price, player_id)

    def best(self, side, suit):
        if side == Side.BUY:
            return self.best_bid(suit)
        return self.best_ask(suit)

    def best_bid(self, suit: int):
        return self.books[suit].best_bid()

    def best_ask(self, suit: int):
        return self.books[suit].best_ask()

    def pop_best_bid(self, suit):
        return self.books[suit].pop_best_bid()

    def pop_best_ask(self, suit):
        return self.books[suit].pop_best_ask()

    def __str__(self):
        return '\\n'.join([f"Suit: {suit}\\n{str(book)}" for suit, book in self.books.items()])
