from collections import defaultdict
from enum import Enum
import math
import random
from typing import Dict, List, Optional, Tuple

import numpy as np

from catan.core.game import Game
from catan.core.models.enums import Action, ActionType
from catan.core.models.player import Color


def best_settlement_build_actions(game, possible_actions: List[Action]):
    prods = game.state.board.map.node_production.items()

    yield_3_tiles = [n[0] for n in filter(lambda x: len(x[1]) > 2, prods)]
    possible_3_yield_tiles = list(
        filter(lambda action: action.value in yield_3_tiles, possible_actions)
    )

    if len(possible_3_yield_tiles) != 0:
        return possible_3_yield_tiles[0:5]

    yield_2_tiles = [n[0] for n in filter(lambda x: len(x[1]) > 1, prods)]
    possible_2_yield_tiles = list(
        filter(lambda action: action.value in yield_2_tiles, possible_actions)
    )

    if len(possible_2_yield_tiles) != 0:
        return possible_2_yield_tiles[0:5]

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

    print(opponent_building_nodes)

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


def actions_heuristic(game, actions: List[Action], trade_eps=0.1) -> List[Action]:
    action_types = map(lambda a: a.action_type, actions)

    if ActionType.BUILD_SETTLEMENT in action_types:
        return best_settlement_build_actions(game, possible_actions=actions)

    # Move robber to the place the worst for the opponents
    if ActionType.MOVE_ROBBER in action_types:
        return best_robber_actions(game, Color.BLUE, n=2)

    if ActionType.MARITIME_TRADE in action_types:
        if random.random() < trade_eps:
            return list(
                filter(lambda a: a.action_type != ActionType.MARITIME_TRADE, actions)
            )

    return actions


# class CatanRewards(Enum):
#      = 10
#     BUILT_CITY = 15
#     OWNS_LONGEST_ROAD_TITLE = 20
#     OWNS_LARGEST_ARMY_TITLE = 20
#     OWNS_DEV_CARD_VP = 10

#     # Activities leading to future rewards
#     BUILT_ROAD = 1
#     BOUGHT_DEV_CARD = 1
#     ACTIVATED_PORT = 3
#     MOVE_ROBBER = 0.1

#     # Penalties
#     LOST_LONGEST_ROAD_TITLE = -30
#     LOST_LARGEST_ARMY_TITLE = -30
#     END_TURN = -0.2

catan_rewards = defaultdict(
    lambda: 1,
    {
        ActionType.BUILD_CITY: 20,
        ActionType.BUILD_SETTLEMENT: 20,
        ActionType.BUILD_ROAD: 2,
        ActionType.BUY_DEVELOPMENT_CARD: 2,
        ActionType.MARITIME_TRADE: 0.01,
        ActionType.MOVE_ROBBER: 0.01,
    },
)


def random_decide(player, game, playable_actions):
    return random.choice(playable_actions)


def weighted_decide(player, game, playable_actions: List[Action]):
    weights = []
    action_indices = []

    for idx, action in enumerate(playable_actions):
        reward = catan_rewards[action.action_type]
        weights.append(reward)
        action_indices.append(idx)

    total_weight = sum(weights)
    probabilities = [w / total_weight for w in weights]

    rand_idx = np.random.choice(action_indices, p=probabilities)

    # print(playable_actions[rand_idx], "Dupa")

    return playable_actions[rand_idx]


class MCTSNode:
    def __init__(
        self,
        game,
        color,
        parent: Optional["MCTSNode"] = None,
        action=None,
    ):
        self.game = game
        self.parent = parent
        self.action: Action = action
        self.color = color
        self.children: List["MCTSNode"] = []
        self.reward = 0
        self.visits = 0
        self.untried_actions = self.game.state.playable_actions.copy()

        self.untried_actions = actions_heuristic(
            game=self.game, actions=self.untried_actions
        )

    def ucb1_score(self, exploration_const=1.4):
        if self.visits == 0:
            return float("inf")

        # UCB1 = (wins / visits) + C * sqrt(log(parent_visits) / visits)
        exploitation_term = self.reward / self.visits
        exploration_term = exploration_const * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )

        return exploitation_term + exploration_term

    def is_fully_expanded(self):
        return len(self.untried_actions) == 0

    def is_terminal_node(self):
        return self.game.finished()

    def select_child(self):
        """Selects child with the highest UCB1 score."""
        if not self.children:
            return None

        return max(self.children, key=lambda child: child.ucb1_score())

    def expand(self):
        """Expands the node by creating one child node for an untried move."""
        if not self.untried_actions:
            return None

        next_action = self.untried_actions.pop()
        next_game = self.game.copy()
        next_game.execute(next_action)

        child_node = MCTSNode(
            game=next_game, parent=self, action=next_action, color=self.color
        )
        self.children.append(child_node)

        return child_node

    def simulate(self):
        return self.game.copy().play(decide_fn=weighted_decide)

    def backpropagate(self, reward):
        self.visits += 1
        self.reward += reward

        if self.parent:
            self.parent.backpropagate(reward)

    def run_playouts(self, n_simulations: int):
        for _ in range(n_simulations):
            node = self

            while (
                node.is_fully_expanded()
                and not node.is_terminal_node()
                and node.children
            ):
                node = node.select_child()

            if not node.is_fully_expanded() and not node.is_terminal_node():
                node = node.expand()

            reward = 0
            winner_color = node.simulate()

            if winner_color == self.color:
                reward = 1
                # reward = map_action_to_reward(node.action)

            node.backpropagate(reward)

    def find_best_action(self):
        best_child = max(self.children, key=lambda child: child.visits)
        return best_child.action

    def get_action_stats_recursive(self, stats: Dict[str, Tuple[int, float]]):
        for child in self.children:
            if child.action is not None:
                action_type = child.action.action_type

                current_visits, current_reward = stats.get(action_type, (0, 0.0))

                stats[action_type] = (
                    current_visits + child.visits,
                    current_reward + child.reward,
                )

            child.get_action_stats_recursive(stats)

    def get_action_stats(self) -> Dict[str, Tuple[int, float]]:
        all_action_type_stats: Dict[str, Tuple[int, float]] = {}
        self.get_action_stats_recursive(all_action_type_stats)
        return all_action_type_stats
