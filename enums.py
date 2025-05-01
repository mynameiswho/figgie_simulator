from enum import Enum


class Suits(Enum):
    HEARTS = 0
    CLUBS = 1
    DIAMONDS = 2
    SPADES = 3

class Side(Enum):
    BUY = 0
    SELL = 1

class FiggieActions(Enum):
    PASS=0
    SHOW=1
    TAKE=2