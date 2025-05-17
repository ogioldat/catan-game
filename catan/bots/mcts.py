import math
import random
from typing import List, Optional

from catan.core.game import Game as CatanGame
from catan.core.models.enums import Action
from catan.core.models.player import Color, Player, RandomPlayer


def random_decide(_, game, playable_actions):
    return random.choice(playable_actions)


class MCTSNode:
    def __init__(
        self,
        game: CatanGame,
        color: Color,
        parent: Optional["MCTSNode"] = None,
        action: Optional[Action] = None,
    ):
        self.game = game
        self.parent = parent
        self.action = action
        self.color = color
        self.children: List["MCTSNode"] = []
        self.wins = 0
        self.visits = 0
        self.untried_actions = self.game.state.playable_actions.copy()[0:5]

    def ucb1_score(self, exploration_const=1.4):
        if self.visits == 0:
            return float("inf")

        # UCB1 = (wins / visits) + C * sqrt(log(parent_visits) / visits)
        exploitation_term = self.wins / self.visits
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

    def simulate(self) -> Color:
        return self.game.copy().play(decide_fn=random_decide)

    def backpropagate(self, reward):
        self.visits += 1
        self.wins += reward

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

            node.backpropagate(reward)

        if not self.children:
            raise RuntimeError("MCTS root node is empty!")

    def find_best_action(self) -> Action:
        best_child = max(self.children, key=lambda child: child.visits)
        return best_child.action
