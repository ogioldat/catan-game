import random
from typing import List
from catan.core.game import Game
from catan.core.models.enums import BRICK, WOOD, Action, ActionType
from catan.core.models.map import NodeId
from catan.core.models.player import Color


def player_has_resource(game: Game, player_color: Color, resource=None):
    if resource is None:
        return True

    buildings = game.state.buildings_by_color[player_color]
    nodes = buildings["SETTLEMENT"] + buildings["CITY"]

    for node in nodes:
        adj_tiles = game.state.board.map.adjacent_tiles[node]
        for adj_tile in adj_tiles:
            if adj_tile.resource == resource:
                return True

    return False


def node_has_resource(game: Game, node: NodeId, resource=None):
    if resource is None:
        return True

    prods = game.state.board.map.node_production

    return resource in prods[node].keys()


def yield_n_and_with_resource(
    game,
    n_yields: int,
    wanted_resource=None,
):
    def filter_fn(prod):
        return len(prod[1]) >= n_yields and node_has_resource(
            game, prod[0], wanted_resource
        )

    return filter_fn


def sort_by_yield_chance(action: Action, game: Game):
    return sum(game.state.board.map.node_production[action.value].values())


def best_settlement_build_actions(
    game: Game, possible_actions: List[Action], player_color: Color
):
    random.shuffle(possible_actions)

    prods = game.state.board.map.node_production.items()

    needed_resource = None

    if not player_has_resource(game, player_color, BRICK):
        needed_resource = BRICK
    elif not player_has_resource(game, player_color, WOOD):
        needed_resource = WOOD

    filter_1 = yield_n_and_with_resource(game, 3, needed_resource)
    yield_3_nodes = [n[0] for n in filter(filter_1, prods)]
    possible_3_yield_nodes = list(
        filter(lambda action: action.value in yield_3_nodes, possible_actions)
    )
    # possible_3_yield_nodes = sorted(
    #     possible_3_yield_nodes, key=lambda n: sort_by_yield_chance(n, game)
    # )

    if len(possible_3_yield_nodes) != 0:
        return possible_3_yield_nodes[0:3]

    filter_2 = yield_n_and_with_resource(game, 2, needed_resource)
    yield_2_nodes = [n[0] for n in filter(filter_2, prods)]
    possible_2_yield_nodes = list(
        filter(lambda action: action.value in yield_2_nodes, possible_actions)
    )
    # possible_2_yield_nodes = sorted(
    #     possible_2_yield_nodes, key=lambda n: sort_by_yield_chance(n, game)
    # )

    if len(possible_2_yield_nodes) != 0:
        return possible_2_yield_nodes[0:4]

    return possible_actions


def best_robber_actions(
    game: Game, player_color: Color, playable_actions: List[Action], n=5
):
    opponent_colors = [p.color for p in game.state.players if p.color != player_color]

    opponent_building_nodes = []

    for op_color in opponent_colors:
        opponent_buildings = game.state.buildings_by_color[op_color]
        opponent_building_nodes += (
            opponent_buildings["SETTLEMENT"] + opponent_buildings["CITY"]
        )

    def buildings_on_tile(entry):
        coords, tile = entry
        tile_nodes = set(tile.nodes.values())

        return len(tile_nodes.intersection(set(opponent_building_nodes)))

    tiles = game.state.board.map.land_tiles.copy().items()
    optimal_tiles = sorted(tiles, key=buildings_on_tile, reverse=True)

    optimal_tiles_coords = list(map(lambda a: a[0], optimal_tiles[0:n]))

    def is_optimal_action(action):
        return action.value[0] in optimal_tiles_coords

    return list(filter(is_optimal_action, playable_actions))


def actions_heuristic(
    game, actions: List[Action], player_color: Color, trade_eps=0.1
) -> List[Action]:
    action_types = map(lambda a: a.action_type, actions)

    if ActionType.BUILD_SETTLEMENT in action_types:
        return best_settlement_build_actions(
            game, possible_actions=actions, player_color=player_color
        )

    if ActionType.MOVE_ROBBER in action_types:
        return best_robber_actions(game, player_color, n=2)

    return actions
