from dataclasses import dataclass
from typing import Any, List
from pprint import pprint

from catan.core.game import Game
from catan.core.models.player import Color


@dataclass(frozen=True)
class PlayerStats:
    color: Color
    player_type: str
    victory_points: int
    longest_road: int
    settlements: Any
    n_settlements: int
    roads: Any
    n_roads: int
    cities: Any
    n_cities: int


def player_stats(game: Game) -> List[PlayerStats]:
    stats = []
    for idx, player in enumerate(game.state.players):
        color = player.color

        building_stats = game.state.buildings_by_color[color]

        stat = PlayerStats(
            color=color,
            player_type=player.__class__.__name__,
            victory_points=game.state.player_state[f"P{idx}_ACTUAL_VICTORY_POINTS"],
            longest_road=game.state.player_state[f"P{idx}_LONGEST_ROAD_LENGTH"],
            settlements=building_stats["SETTLEMENT"],
            n_settlements=len(building_stats["SETTLEMENT"]),
            roads=building_stats["ROAD"],
            n_roads=len(building_stats["ROAD"]),
            cities=building_stats["CITY"],
            n_cities=len(building_stats["CITY"]),
        )

        stats.append(stat)
    return stats


def print_player_stats(stats):
    pprint(stats, compact=True, underscore_numbers=True, sort_dicts=True)
