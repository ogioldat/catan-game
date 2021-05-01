import random
import time

from catanatron.models.enums import BuildingType, DevelopmentCard, Resource
from catanatron.game import Game
from catanatron.models.player import Player
from catanatron.models.actions import ActionType
from catanatron.models.enums import Resource, DevelopmentCard
from experimental.machine_learning.features import (
    build_production_features,
    iter_players,
    reachability_features,
)
from experimental.machine_learning.players.tree_search_utils import expand_spectrum


TRANSLATE_VARIETY = 4  # i.e. each new resource is like 4 production points
production_features = build_production_features(True)


def value_production(sample, player_name="P0", include_variety=True):
    proba_point = 2.778 / 100
    features = [
        f"EFFECTIVE_{player_name}_WHEAT_PRODUCTION",
        f"EFFECTIVE_{player_name}_ORE_PRODUCTION",
        f"EFFECTIVE_{player_name}_SHEEP_PRODUCTION",
        f"EFFECTIVE_{player_name}_WOOD_PRODUCTION",
        f"EFFECTIVE_{player_name}_BRICK_PRODUCTION",
    ]
    prod_sum = sum([sample[f] for f in features])
    prod_variety = (
        sum([sample[f] != 0 for f in features]) * TRANSLATE_VARIETY * proba_point
    )
    return prod_sum + (0 if not include_variety else prod_variety)


def base_value_function(params):
    def fn(game, p0_color):
        iterator = iter_players(game, p0_color)
        _, p0 = next(iterator)

        our_production_sample = production_features(game, p0_color)
        enemy_production_sample = production_features(game, p0_color)
        production = value_production(our_production_sample, "P0")
        enemy_production = value_production(enemy_production_sample, "P1", False)

        longest_road_length = game.state.players_by_color[p0_color].longest_road_length

        features = [f"P0_1_ROAD_REACHABLE_{resource.value}" for resource in Resource]
        reachability_sample = reachability_features(game, p0_color, 2)
        reachable_production_at_one = sum([reachability_sample[f] for f in features])

        return float(
            p0.public_victory_points * 1000000
            + longest_road_length * 10
            + len(p0.development_deck.to_array()) * 10
            + len(p0.played_development_cards.to_array()) * 10.1
            + p0.played_development_cards.count(DevelopmentCard.KNIGHT) * 10.1
            + production * 1000
            - enemy_production * 1000
            + reachable_production_at_one * 10
        )

    return fn


DEFAULT_WEIGHTS = [1e10, 1e8, 1e8, 1e4, 1e3, 10]


def contender_value_function(params):
    def fn(game, p0_color):
        iterator = iter_players(game, p0_color)
        _, p0 = next(iterator)

        production_features = build_production_features(True)
        our_production_sample = production_features(game, p0_color)
        enemy_production_sample = production_features(game, p0_color)
        production = value_production(our_production_sample, "P0")
        enemy_production = value_production(enemy_production_sample, "P1", False)

        longest_road_length = game.state.players_by_color[p0_color].longest_road_length

        features = [f"P0_1_ROAD_REACHABLE_{resource.value}" for resource in Resource]
        reachability_sample = reachability_features(game, p0_color, 2)
        reachable_production_at_one = sum([reachability_sample[f] for f in features])

        # hand_sample = resource_hand_features(game, p0_color)
        # features = [f"P0_{resource.value}_IN_HAND" for resource in Resource]
        num_in_hand = p0.resource_deck.num_cards()
        if num_in_hand > 7:
            hand_contribution = num_in_hand * -params[4]
        else:
            hand_contribution = num_in_hand * params[4]

        num_buildable_nodes = len(game.state.board.buildable_node_ids(p0_color))
        longest_road_factor = params[5] if num_buildable_nodes == 0 else 0.1
        return float(
            p0.public_victory_points * params[0]
            + production * params[1]
            - enemy_production * params[2]
            + reachable_production_at_one * params[3]
            # TODO: buildable nodes. or closeness to city or settlement.
            + hand_contribution
            + longest_road_length * longest_road_factor
            + len(p0.development_deck.to_array()) * 10
            + len(p0.played_development_cards.to_array()) * 10.1
            + p0.played_development_cards.count(DevelopmentCard.KNIGHT) * 10.1
        )

    return fn


def get_value_fn(name, params):
    if name is None or params is None:
        return base_value_function(DEFAULT_WEIGHTS)
    return globals()[name](params)


class ValueFunctionPlayer(Player):
    def __init__(self, color, name, value_fn_builder_name=None, params=DEFAULT_WEIGHTS):
        super().__init__(color, name=name)
        self.value_fn_builder_name = (
            "contender_value_function"
            if value_fn_builder_name == "C"
            else "base_value_function"
        )
        self.params = params

    def decide(self, game: Game, playable_actions):
        if len(playable_actions) == 1:
            return playable_actions[0]

        best_value = float("-inf")
        best_action = None
        for action in playable_actions:
            game_copy = game.copy()
            game_copy.execute(action)

            value_fn = get_value_fn(self.value_fn_builder_name, self.params)
            value = value_fn(game_copy, self.color)
            if value > best_value:
                best_value = value
                best_action = action

        return best_action

    def __str__(self) -> str:
        return super().__str__() + self.value_fn_builder_name + str(self.params)


class VictoryPointPlayer(Player):
    def decide(self, game: Game, playable_actions):
        if len(playable_actions) == 1:
            return playable_actions[0]

        best_value = float("-inf")
        best_actions = []
        for action in playable_actions:
            game_copy = game.copy()
            game_copy.execute(action)

            value = game_copy.state.players_by_color[self.color].actual_victory_points
            if value == best_value:
                best_actions.append(action)
            if value > best_value:
                best_value = value
                best_actions = [action]

        return random.choice(best_actions)


ALPHABETA_DEFAULT_DEPTH = 2
MAX_SEARCH_TIME_SECS = 20


class AlphaBetaPlayer(Player):
    def __init__(
        self,
        color,
        name,
        depth=ALPHABETA_DEFAULT_DEPTH,
        prunning=False,
        value_fn_builder_name=None,
        params=DEFAULT_WEIGHTS,
    ):
        super().__init__(color, name=name)
        self.depth = int(depth)
        self.prunning = str(prunning).lower() != "false"
        self.value_fn_builder_name = (
            "contender_value_function"
            if value_fn_builder_name == "C"
            else "base_value_function"
        )
        self.params = params

    def get_actions(self, game):
        if self.prunning:
            return list_prunned_actions(game)
        return game.state.playable_actions

    def decide(self, game: Game, playable_actions):
        actions = self.get_actions(game)
        if len(actions) == 1:
            return actions[0]

        start = time.time()
        deadline = start + MAX_SEARCH_TIME_SECS
        result = self.alphabeta(
            game.copy(),
            self.depth,
            float("-inf"),
            float("inf"),
            deadline,
        )
        # print("Decision Results:", self.depth, len(actions), time.time() - start)
        # breakpoint()
        return result[0]

    def __repr__(self) -> str:
        return (
            super().__repr__()
            + f"(depth={self.depth},value_fn={self.value_fn_builder_name},prunning={self.prunning})"
        )

    def alphabeta(self, game, depth, alpha, beta, deadline):
        """AlphaBeta MiniMax Algorithm.

        NOTE: Sometimes returns a value, sometimes an (action, value). This is
        because some levels are state=>action, some are action=>state and in
        action=>state would probably need (action, proba, value) as return type.
        """
        if depth == 0 or game.winning_color() is not None or time.time() >= deadline:
            value_fn = get_value_fn(self.value_fn_builder_name, self.params)
            return value_fn(game, self.color)

        maximizingPlayer = game.state.current_player().color == self.color
        actions = self.get_actions(game)
        children = expand_spectrum(game, actions)
        if maximizingPlayer:
            best_action = None
            best_value = float("-inf")
            for action, outprobas in children.items():
                expected_value = 0
                for (out, proba) in outprobas:
                    result = self.alphabeta(out, depth - 1, alpha, beta, deadline)
                    value = result if isinstance(result, float) else result[1]
                    expected_value += proba * value

                if expected_value > best_value:
                    best_action = action
                    best_value = expected_value
                alpha = max(alpha, best_value)
                if alpha >= beta:
                    break  # beta cutoff

            return best_action, best_value
        else:
            best_action = None
            best_value = float("inf")
            for action, outprobas in children.items():
                expected_value = 0
                for (out, proba) in outprobas:
                    result = self.alphabeta(out, depth - 1, alpha, beta, deadline)
                    value = result if isinstance(result, float) else result[1]
                    expected_value += proba * value

                if expected_value < best_value:
                    best_action = action
                    best_value = expected_value
                beta = min(beta, best_value)
                if beta <= alpha:
                    break  # alpha cutoff

            return best_action, best_value


def list_prunned_actions(game):
    current_color = game.state.current_player().color
    playable_actions = game.state.playable_actions
    actions = playable_actions.copy()
    types = set(map(lambda a: a.action_type, playable_actions))

    # Prune Initial Settlements at 1-tile places
    if (
        ActionType.BUILD_FIRST_SETTLEMENT in types
        or ActionType.BUILD_SECOND_SETTLEMENT in types
    ):
        actions = filter(
            lambda a: len(game.state.board.map.adjacent_tiles[a.value]) != 1, actions
        )

    # Prune Trading if can hold for resources. Only for rare resources.
    if ActionType.MARITIME_TRADE in types:
        port_resources = game.state.board.get_player_port_resources(current_color)
        has_three_to_one = None in port_resources
        # TODO: for 2:1 ports, skip any 3:1 or 4:1 trades
        # TODO: if can_safely_hold, prune all
        tmp_actions = []
        for action in actions:
            if action.action_type != ActionType.MARITIME_TRADE:
                tmp_actions.append(action)
                continue
            # has 3:1, skip any 4:1 trades
            if has_three_to_one and action.value[3] is not None:
                continue
            tmp_actions.append(action)
        actions = tmp_actions

    if ActionType.MOVE_ROBBER in types:
        actions = prune_robber_actions(
            current_color, game, actions, ActionType.MOVE_ROBBER
        )
    if ActionType.PLAY_KNIGHT_CARD in types:
        actions = prune_robber_actions(
            current_color, game, actions, ActionType.PLAY_KNIGHT_CARD
        )

    return list(actions)


def prune_robber_actions(current_color, game, actions, action_type):
    """Eliminate all but the most impactful tile"""
    enemy = next(filter(lambda p: p.color != current_color, game.state.players))
    enemy_owned_tiles = set()
    for node_id in enemy.buildings[BuildingType.SETTLEMENT]:
        enemy_owned_tiles.update(game.state.board.map.adjacent_tiles[node_id])
    for node_id in enemy.buildings[BuildingType.CITY]:
        enemy_owned_tiles.update(game.state.board.map.adjacent_tiles[node_id])

    robber_moves = filter(
        lambda a: a.action_type == action_type
        and game.state.board.map.tiles[a.value[0]] in enemy_owned_tiles,
        actions,
    )
    production_features = build_production_features(True)

    def impact(action):
        game_copy = game.copy()
        game_copy.execute(action)

        our_production_sample = production_features(game_copy, current_color)
        enemy_production_sample = production_features(game_copy, current_color)
        production = value_production(our_production_sample, "P0")
        enemy_production = value_production(enemy_production_sample, "P1")

        return enemy_production - production

    most_impactful_robber_action = max(
        robber_moves, key=impact
    )  # most production and variety producing
    actions = filter(
        lambda a: a.action_type != action_type or a == most_impactful_robber_action,
        actions,
    )
    return actions
