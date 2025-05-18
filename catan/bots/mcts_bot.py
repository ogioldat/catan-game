from typing import List
import catan.bots.mcts as mcts

from catan.core.models.enums import Action, ActionType
from catan.core.models.player import Player


def fast_forward_decide(playable_actions: List[Action]):
    action_types = set([a.action_type for a in playable_actions])

    if len(action_types) == 1 and (
        ActionType.END_TURN in action_types or ActionType.ROLL in action_types
    ):
        return playable_actions[0]

    return None


class MCTSBot(Player):
    def __init__(self, color, n_simulations=100, debug=False, debug_cb=None):
        super().__init__(color, is_bot=True)

        self.n_simulations = n_simulations
        self.debug = debug
        self.debug_cb = debug_cb

    def decide(
        self,
        game,
        playable_actions,
    ):
        ff_action = fast_forward_decide(playable_actions)
        if ff_action:
            return ff_action

        mcts_root = mcts.MCTSNode(game=game.copy(), color=self.color)

        if self.debug_cb:
            self.debug_cb(mcts_root)

        mcts_root.run_playouts(n_simulations=self.n_simulations)
        best_action = mcts_root.find_best_action()

        if self.debug:
            print(
                f"Move {game.state.num_turns}: MCTS bot performed action {best_action}"
            )

        return best_action
