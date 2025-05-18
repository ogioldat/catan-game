import json
from typing import Literal
from flask import Response, Blueprint, jsonify, abort, request

from catan.bots.mcts_bot import MCTSBot
from catan.core.models.map import DEFAULT_MAP
from catan.server.models import upsert_game_state, get_game_state
from catan.core.json import GameEncoder, action_from_json
from catan.core.models.player import Color, RandomPlayer
from catan.core.game import Game

bp = Blueprint("api", __name__, url_prefix="/api")


def player_factory(player_keys: Literal["MCTS", "RANDOM"]):
    players = []
    for player, color in zip(player_keys, Color):
        if player == "MCTS":
            players.append(MCTSBot(color=color, n_simulations=5))

        if player == "RANDOM":
            players.append(RandomPlayer(color=color))

    return players


@bp.route("/games", methods=("POST",))
def post_game_endpoint():
    player_keys = request.json["players"]
    players = player_factory(player_keys)

    game = Game(players=players, catan_map=DEFAULT_MAP)

    upsert_game_state(game)
    return jsonify({"game_id": game.id})


@bp.route("/games/<string:game_id>/states/<string:state_index>", methods=("GET",))
def get_game_endpoint(game_id, state_index):
    state_index = None if state_index == "latest" else int(state_index)
    game = get_game_state(game_id, state_index)
    if game is None:
        abort(404, description="Resource not found")

    return Response(
        response=json.dumps(game, cls=GameEncoder),
        status=200,
        mimetype="application/json",
    )


@bp.route("/games/<string:game_id>/actions", methods=["POST"])
def post_action_endpoint(game_id):
    game = get_game_state(game_id)
    if game is None:
        abort(404, description="Resource not found")

    if game.winning_color() is not None:
        return Response(
            response=json.dumps(game, cls=GameEncoder),
            status=200,
            mimetype="application/json",
        )

    body_is_empty = (not request.data) or request.json is None
    if game.state.current_player().is_bot or body_is_empty:
        game.play_tick()
        upsert_game_state(game)
    else:
        action = action_from_json(request.json)
        game.execute(action)
        upsert_game_state(game)

    return Response(
        response=json.dumps(game, cls=GameEncoder),
        status=200,
        mimetype="application/json",
    )


# ===== Debugging Routes
# @app.route(
#     "/games/<string:game_id>/players/<int:player_index>/features", methods=["GET"]
# )
# def get_game_feature_vector(game_id, player_index):
#     game = get_game_state(game_id)
#     if game is None:
#         abort(404, description="Resource not found")

#     return create_sample(game, game.state.colors[player_index])


# @app.route("/games/<string:game_id>/value-function", methods=["GET"])
# def get_game_value_function(game_id):
#     game = get_game_state(game_id)
#     if game is None:
#         abort(404, description="Resource not found")

#     # model = tf.keras.models.load_model("data/models/mcts-rep-a")
#     model2 = tf.keras.models.load_model("data/models/mcts-rep-b")
#     feature_ordering = get_feature_ordering()
#     indices = [feature_ordering.index(f) for f in NUMERIC_FEATURES]
#     data = {}
#     for color in game.state.colors:
#         sample = create_sample_vector(game, color)
#         # scores = model.call(tf.convert_to_tensor([sample]))

#         inputs1 = [create_board_tensor(game, color)]
#         inputs2 = [[float(sample[i]) for i in indices]]
#         scores2 = model2.call(
#             [tf.convert_to_tensor(inputs1), tf.convert_to_tensor(inputs2)]
#         )
#         data[color.value] = float(scores2.numpy()[0][0])

#     return data
