from collections import defaultdict
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from catan.bots.mcts import MCTSNode
from catan.bots.mcts_bot import MCTSBot
from catan.core.game import Game
from catan.core.models.enums import Action, ActionType
from catan.core.models.player import Color, RandomPlayer


def plot_action_freqs(actions: List[Action], exclusions: List[str] = []):
    player_action_counts = defaultdict(lambda: defaultdict(int))
    all_action_types = set()
    all_players = set()

    for action in actions:
        player, action_type, _ = action

        if action_type.name in exclusions:
            continue

        player_action_counts[player][action_type.name] += 1
        all_action_types.add(action_type.name)
        all_players.add(player)

    n_action_types = len(all_action_types)
    n_players = len(all_players)

    player_plot_data = {}
    for player in all_players:
        player_plot_data[player] = [
            player_action_counts[player].get(action_type, 0)
            for action_type in all_action_types
        ]

    player_bar_colors = {
        Color.RED: "red",
        Color.BLUE: "blue",
        Color.ORANGE: "orange",
        Color.VIOLET: "violet",
    }

    # Plotting
    x_indices = np.arange(n_action_types)  # the label locations for action types
    bar_width = (
        0.8 / n_players
    )  # the width of the bars, adjusted for the number of players

    fig, ax = plt.subplots(figsize=(8, 6))  # Adjust figure size for better readability

    for i, player in enumerate(all_players):
        # Calculate the offset for each player's bars within a group
        offset = (i - (n_players - 1) / 2) * bar_width
        counts = player_plot_data[player]

        bar_color = player_bar_colors.get(player, None)

        rects = ax.bar(
            x_indices + offset,
            counts,
            bar_width,
            label=player,
            color=bar_color,
            alpha=0.7,
        )
        ax.bar_label(rects, padding=3)

    # Add labels, title, and legend
    ax.set_ylabel("Frequency of Actions")
    ax.set_xlabel("Type of Action")
    ax.set_title("Action Frequencies per Player")
    ax.set_xticks(x_indices)
    ax.set_xticklabels(
        all_action_types, rotation=45, ha="right"
    )  # Rotate labels if they overlap
    ax.legend(title="Player")
    fig.tight_layout()

    return fig, ax


def plot_mcts_n_sim_win_rate(
    mcts_color: Color = Color.BLUE,
    sim_range=np.arange(2, 12, 4),
    games_per_sim=5,
):
    n_playouts = len(sim_range)
    mcts_win_rates = np.zeros(n_playouts)

    for idx, n_sim in enumerate(sim_range):
        mcts_playout_wins = 0
        for _ in range(games_per_sim):
            game = Game(
                players=[
                    RandomPlayer(color=Color.RED, is_bot=True),
                    MCTSBot(color=Color.BLUE, n_simulations=n_sim),
                ]
            )
            winner_color = game.play()

            if winner_color == mcts_color:
                mcts_playout_wins += 1

        mcts_win_rates[idx] = mcts_playout_wins / games_per_sim

    plt.scatter(sim_range, mcts_win_rates)
    plt.show()


def get_mcts_sims_stats(roots: List[MCTSNode], keys=None, kind="visit"):
    data_for_df = []
    stats = map(lambda r: r.get_action_stats(), roots)

    for sim_idx, sim_stats in enumerate(stats):
        record = {"SIM_NUM": sim_idx + 1}
        not_empty = False
        for action_type, (visits, reward) in sim_stats.items():
            if keys and action_type not in keys:
                continue

            if kind == "visit":
                record[action_type.value] = visits
            else:
                record[action_type.value] = reward

            if visits > 0:
                not_empty = True

        if not_empty:
            data_for_df.append(record)

    return pd.DataFrame(data_for_df)
