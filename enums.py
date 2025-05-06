from enum import Enum
from dataclasses import dataclass


class FiggieSuit(Enum):
    HEARTS = 0
    CLUBS = 1
    DIAMONDS = 2
    SPADES = 3


class FiggieSide(Enum):
    BUY = 0
    SELL = 1


class FiggieInGameAction(Enum):
    PASS=0
    SHOW=1
    TAKE=2


@dataclass
class FiggieAction:
    action: FiggieInGameAction
    suit: FiggieSuit
    acting_intent_side: FiggieSide
    price: int