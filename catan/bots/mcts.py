import math
import random
from typing import List, Any, Optional, Protocol, Tuple, Dict

from catan.core.game import Game as CatanGame
from catan.core.models.player import Color, Player as CatanPlayer
from catan.core.models.enums import Action as CatanAction

# Define player IDs (can be customized)
PLAYER_ONE = 1
PLAYER_TWO = -1


class MCTSGameState(Protocol):
    """
    A protocol defining the interface for a game state.
    MCTS will interact with the game through this interface.
    Implement this protocol for your specific game.
    """

    def get_current_player(self) -> int:
        """
        Returns the player whose turn it is in the current state.
        (e.g., PLAYER_ONE or PLAYER_TWO)
        """
        ...

    def get_possible_actions(self) -> List[Any]:
        """
        Returns a list of all valid actions from the current state.
        """
        ...

    def take_action(self, action: Any) -> "MCTSGameState":
        """
        Takes an action and returns a *new* GameState object representing the state after the action.
        This method should handle switching the current player.
        It's crucial that this returns a new instance or a deep copy if the state is mutable.
        """
        ...

    def is_terminal(self) -> bool:
        """
        Checks if the current state is a terminal state (game over).
        """
        ...

    def get_game_result(self) -> float:
        """
        If the state is terminal, returns the outcome of the game from PLAYER_ONE's perspective.
        - Return 1.0 if PLAYER_ONE wins.
        - Return -1.0 if PLAYER_TWO wins (PLAYER_ONE loses).
        - Return 0.0 for a draw.
        - Behavior is undefined if the state is not terminal.
        """
        ...

    def __str__(self) -> str:
        """Optional: For debugging and visualization."""
        return "GameState"

    def __hash__(self) -> int:
        """
        Optional but recommended if you plan to use states as dictionary keys
        for memoization or transposition tables outside of this MCTS node structure.
        The MCTS nodes themselves are distinct objects.
        """
        return id(self)

    def __eq__(self, other: object) -> bool:
        """Optional: For comparing states."""
        if not isinstance(other, MCTSGameState):
            return NotImplemented
        return self is other


class MCTSNode:
    """
    Represents a node in the Monte Carlo Search Tree.
    """

    def __init__(
        self,
        state: MCTSGameState,
        parent: Optional["MCTSNode"] = None,
        action_taken: Optional[Any] = None,
    ):
        self.state: MCTSGameState = state
        self.parent: Optional[MCTSNode] = parent
        self.action_taken: Optional[Any] = (
            action_taken  # The action that led to this state
        )

        self.children: List[MCTSNode] = []

        self.value: float = 0.0
        self.visits: int = 0

        self.untried_actions: List[Any] = list(self.state.get_possible_actions())

        random.shuffle(
            self.untried_actions
        )  # Shuffle for randomness in expansion order

    def is_fully_expanded(self) -> bool:
        """Checks if all possible actions from this node have been expanded."""
        return not self.untried_actions

    def select_child_uct(self, exploration_constant: float) -> "MCTSNode":
        """
        Selects the child with the highest UCT score.
        Assumes this node is fully expanded and its children have been visited at least once.
        The value of the child is from the child's player's perspective.
        The parent (self) wants to choose a child that is good for self.
        If child's player is opponent, then parent wants to minimize child's value (maximize -child.value).
        """
        if not self.children:
            # This should not happen if called on a fully expanded node with children
            raise ValueError("Node has no children to select from.")

        best_child: Optional[MCTSNode] = None
        best_uct_score: float = -float("inf")

        epsilon = 1e-6

        for child in self.children:
            if child.visits == 0:
                uct_score = float("inf")
            else:
                exploitation_term = -(child.value / child.visits)
                exploration_term = exploration_constant * math.sqrt(
                    math.log(self.visits + epsilon) / (child.visits + epsilon)
                )
                uct_score = exploitation_term + exploration_term

            if uct_score > best_uct_score:
                best_uct_score = uct_score
                best_child = child

        if best_child is None:
            return (
                random.choice(self.children) if self.children else self
            )  # Should not happen
        return best_child

    def expand(self) -> "MCTSNode":
        """
        Expands the current node by creating one new child node from an untried action.
        Returns the newly created child node.
        Assumes the current node is not terminal and not fully expanded.
        """
        if not self.untried_actions:
            raise RuntimeError("Cannot expand a fully expanded node.")

        action = self.untried_actions.pop()
        next_state = self.state.take_action(action)
        child_node = MCTSNode(next_state, parent=self, action_taken=action)
        self.children.append(child_node)
        return child_node

    def update(self, reward_for_current_player_at_this_node: float):
        """
        Updates the node's visit count and accumulated value.
        The reward is from the perspective of self.state.get_current_player().
        """
        self.visits += 1
        self.value += reward_for_current_player_at_this_node

    def __str__(self):
        return (
            f"Node(State:\n{self.state},\n"
            f"Visits: {self.visits}, Value: {self.value:.2f}, "
            f"Untried: {len(self.untried_actions)}, Children: {len(self.children)})"
        )


class MCTS:
    """
    Monte Carlo Tree Search algorithm.
    """

    def __init__(
        self, exploration_constant: float = 1.414
    ):  # sqrt(2) is a common value
        self.exploration_constant = exploration_constant

    def _select_promising_node(self, root_node: MCTSNode) -> MCTSNode:
        """
        Traverses the tree from the root, selecting nodes based on UCT,
        until a leaf node (not fully expanded or terminal) is reached.
        """
        node = root_node
        while not node.state.is_terminal():
            if not node.is_fully_expanded():
                return node.expand()  # Expand and return the new child
            else:
                if (
                    not node.children
                ):  # Should not happen for a non-terminal, fully expanded node
                    return node  # Terminal or stuck
                node = node.select_child_uct(self.exploration_constant)
        return (
            node  # Returns a terminal node or a fully expanded path ending in terminal
        )

    def _simulate_random_playout(self, state: MCTSGameState) -> float:
        """
        Simulates a random playout from the given state until a terminal state is reached.
        Returns the game result from the perspective of state.get_current_player().
        """
        current_state = state
        player_at_simulation_start = state.get_current_player()

        if current_state.is_terminal():  # If simulation starts from a terminal state
            game_result_p1_perspective = current_state.get_game_result()
            if player_at_simulation_start == PLAYER_ONE:
                return game_result_p1_perspective
            else:  # PLAYER_TWO
                return -game_result_p1_perspective

        while not current_state.is_terminal():
            possible_actions = current_state.get_possible_actions()
            if not possible_actions:
                # Should not happen in a well-defined game if not terminal
                # Consider it a draw or a loss for the current player if stuck
                return 0.0
            action = random.choice(possible_actions)
            current_state = current_state.take_action(action)

        # Game is now terminal
        game_result_p1_perspective = (
            current_state.get_game_result()
        )  # Outcome for PLAYER_ONE

        # Convert reward to the perspective of the player who was current at the *start* of the simulation
        if player_at_simulation_start == PLAYER_ONE:
            return game_result_p1_perspective
        else:  # player_at_simulation_start == PLAYER_TWO
            return -game_result_p1_perspective

    def _backpropagate(
        self, node_where_simulation_started: MCTSNode, reward_for_sim_initiator: float
    ):
        """
        Backpropagates the simulation result up the tree from the node_where_simulation_started.
        `reward_for_sim_initiator` is from the perspective of
        `node_where_simulation_started.state.get_current_player()`.
        """
        current_node: Optional[MCTSNode] = node_where_simulation_started

        while current_node is not None:
            # The reward needs to be from the perspective of current_node.state.get_current_player()
            reward_for_current_node_player = 0.0
            if (
                current_node.state.get_current_player()
                == node_where_simulation_started.state.get_current_player()
            ):
                reward_for_current_node_player = reward_for_sim_initiator
            else:  # Opponent's turn at current_node compared to sim_start_node
                reward_for_current_node_player = -reward_for_sim_initiator

            current_node.update(reward_for_current_node_player)
            current_node = current_node.parent

    def simulate(self, initial_state: MCTSGameState, num_simulations: int) -> Any:
        """
        Performs MCTS for a given number of simulations from the initial state.
        Returns the best action found.
        """
        if initial_state.is_terminal():
            raise ValueError("Cannot perform MCTS search from a terminal state.")
        if not initial_state.get_possible_actions():
            raise ValueError("No possible actions from the initial state.")

        root_node = MCTSNode(state=initial_state)

        if num_simulations == 0:
            return random.choice(root_node.state.get_possible_actions())

        for _ in range(num_simulations):
            promising_node = self._select_promising_node(root_node)

            simulation_reward = self._simulate_random_playout(promising_node.state)

            self._backpropagate(promising_node, simulation_reward)

        if not root_node.children:
            return random.choice(initial_state.get_possible_actions())

        best_child_node: Optional[MCTSNode] = None
        most_visits = -1
        for child in root_node.children:
            if child.visits > most_visits:
                most_visits = child.visits
                best_child_node = child

        if best_child_node and best_child_node.action_taken is not None:
            return best_child_node.action_taken
        else:
            # Fallback if something unexpected happened (e.g., no children, or best child has no action)
            # This should ideally not be reached with proper MCTS execution.
            print(
                "Warning: MCTS couldn't determine a best child reliably. Falling back to random."
            )
            return random.choice(initial_state.get_possible_actions())


class MCTSCatanGameState:
    game: CatanGame
    seed: int

    def __init__(self, players, game=None, seed=0):
        self.seed = seed

        if len(players) != 2:
            raise ValueError("2 player play-outs supported only!")

        if game is None:
            self.game = CatanGame(players=players, seed=seed)
        else:
            self.game = game

    def get_current_player(self) -> int:
        return self.game.state.current_player()

    def get_possible_actions(self) -> List[CatanAction]:
        return self.game.state.playable_actions

    def take_action(self, action: CatanAction) -> "MCTSCatanGameState":
        next_game = self.game.copy()
        next_game.execute(action)

        return MCTSCatanGameState(
            players=next_game.state.players, game=next_game, seed=self.seed
        )

    def _check_winner(self) -> Optional[int]:
        if self._winner is not None:  # Use cached winner
            return self._winner

        # Check rows
        for r in range(3):
            if (
                self.board[r][0] != 0
                and self.board[r][0] == self.board[r][1] == self.board[r][2]
            ):
                self._winner = self.board[r][0]
                return self._winner
        # Check columns
        for c in range(3):
            if (
                self.board[0][c] != 0
                and self.board[0][c] == self.board[1][c] == self.board[2][c]
            ):
                self._winner = self.board[0][c]
                return self._winner
        # Check diagonals
        if (
            self.board[0][0] != 0
            and self.board[0][0] == self.board[1][1] == self.board[2][2]
        ):
            self._winner = self.board[0][0]
            return self._winner
        if (
            self.board[0][2] != 0
            and self.board[0][2] == self.board[1][1] == self.board[2][0]
        ):
            self._winner = self.board[0][2]
            return self._winner

        # Check for draw (no empty cells left and no winner)
        if not any(0 in row for row in self.board):
            self._winner = 0  # Draw
            return self._winner

        return None  # No winner yet, game not over or not a draw

    def is_terminal(self) -> bool:
        return self.game.finished()

    def get_game_result(self) -> float:
        winner = self.game.winning_color()

        if winner == self.game.state.players[0].color:
            return 1.0
        elif winner == self.game.state.players[1].color:
            return -1.0
        elif winner is None:
            return 0.0
        else:
            raise RuntimeError("get_game_result called on a non-terminal state.")

    def __str__(self) -> str:
        return "cinżko"

    # For hashing and equality if needed, though MCTS nodes are distinct.
    # A simple tuple representation of the board can be used for hashing.
    def __hash__(self):
        return hash((tuple(map(tuple, self.board)), self._current_player))

    def __eq__(self, other):
        if not isinstance(other, MCTSCatanGameState):
            return NotImplemented
        return (
            self.board == other.board and self._current_player == other._current_player
        )
