from collections import defaultdict
import math
import random
from typing import Dict, List, Optional, Tuple

import numpy as np

from catan.bots.heuristics import actions_heuristic
from catan.core.game import Game
from catan.core.models.enums import Action, ActionType
from catan.core.models.player import Color


catan_weights = defaultdict(
    lambda: 1,
    {
        ActionType.BUILD_CITY: 20,
        ActionType.BUILD_SETTLEMENT: 30,
        ActionType.BUILD_ROAD: 5,
        ActionType.BUY_DEVELOPMENT_CARD: 2,
        ActionType.MARITIME_TRADE: 0.02,
    },
)


def map_action_to_reward(action: Action, game: Game, color: Color) -> int:
    if action.action_type == ActionType.BUILD_ROAD:
        buildings = game.state.buildings_by_color[color]
        num_roads = len(buildings.get("ROAD")) if buildings.get("ROAD") else 0.1
        num_cities = len(buildings.get("CITY")) if buildings.get("CITY") else 0.1
        num_settlements = (
            len(buildings.get("SETTLEMENT")) if buildings.get("CITY") else 0.1
        )

        return num_roads / (num_cities + num_settlements)

    return catan_weights[action.action_type]


def random_decide(player, game, playable_actions):
    return random.choice(playable_actions)


def weighted_decide(player, game, playable_actions: List[Action]):
    weights = []
    action_indices = []

    for idx, action in enumerate(playable_actions):
        reward = catan_weights[action.action_type]
        weights.append(reward)
        action_indices.append(idx)

    total_weight = sum(weights)
    probabilities = [w / total_weight for w in weights]

    rand_idx = np.random.choice(action_indices, p=probabilities)

    return playable_actions[rand_idx]


class MCTSNode:
    def __init__(
        self,
        game: Game,
        color,
        parent: Optional["MCTSNode"] = None,
        action=None,
    ):
        self.game: Game = game
        self.parent = parent
        self.action: Action = action
        self.color = color
        self.children: List["MCTSNode"] = []
        self.reward = 0
        self.visits = 0
        self.untried_actions = self.game.state.playable_actions.copy()

        self.untried_actions = actions_heuristic(
            game=self.game, actions=self.untried_actions, player_color=self.color
        )
        self.current_color: Color = game.state.current_color()

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

            if self.current_color == self.color and winner_color == self.color:
                reward = 1
                node.reward += map_action_to_reward(
                    node.action, self.game, self.current_color
                )

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
