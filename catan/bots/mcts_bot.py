import catan.bots.mcts as mcts
from catan.core.models.player import Player


class MCTSBot(Player):
    def __init__(self, color, n_simulations=100, debug=False):
        super().__init__(color, is_bot=True)

        self.n_simulations = n_simulations
        self.debug = debug

    def decide(self, game, playable_actions):
        mcts_root = mcts.MCTSNode(game=game.copy(), color=self.color)
        mcts_root.run_playouts(n_simulations=self.n_simulations)
        best_action = mcts_root.find_best_action()

        print(f"Move {game.state.num_turns}: MCTS bot performed action {best_action}")

        return best_action
