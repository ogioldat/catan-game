from catanatron import ActionType, Color, RandomPlayer, Game, GameAccumulator
from catanatron.state_functions import get_actual_victory_points
from catanatron.game import TURNS_LIMIT


def test_accumulators():
    players = [
        RandomPlayer(Color.RED),
        RandomPlayer(Color.BLUE),
        RandomPlayer(Color.WHITE),
        RandomPlayer(Color.ORANGE),
    ]
    game = Game(players)

    class MyAccumulator(GameAccumulator):
        def __init__(self):
            self.games = []
            self.actions = []
            self.initialized = False
            self.finalized = False
            self.final_game = None

        def before(self, game):
            self.initialized = True

        def step(self, game, action):
            self.games.append(game.copy())
            self.actions.append(action)

        def after(self, game):
            self.final_game = game
            self.finalized = True

    accumulator = MyAccumulator()
    game.play(accumulators=[accumulator])

    assert accumulator.initialized
    assert len(accumulator.actions) == len(game.state.actions)
    assert accumulator.finalized

    # assert games in step() are before actions are taken
    discard_actions = [
        (i, a)
        for i, a in enumerate(game.state.actions)
        if a.action_type == ActionType.DISCARD
    ]
    for index, action in discard_actions:
        game_snapshot = accumulator.games[index]
        assert game_snapshot.state.is_discarding

    # assert someone wins
    assert accumulator.final_game is not None
    points = [
        get_actual_victory_points(accumulator.final_game.state, color)
        for color in game.state.colors
    ]
    assert (
        any([p >= 10 for p in points])
        or accumulator.final_game.state.num_turns >= TURNS_LIMIT
    )
