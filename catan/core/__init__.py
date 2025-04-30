"""
This is to allow an API like:

from catanatron import Game, Player, Color
"""

from catan.core.game import Game
from catan.core.models.player import Player, HumanPlayer, Color, RandomPlayer
from catan.core.models.enums import (
    Action,
    ActionType,
    WOOD,
    BRICK,
    SHEEP,
    WHEAT,
    ORE,
    RESOURCES,
)
