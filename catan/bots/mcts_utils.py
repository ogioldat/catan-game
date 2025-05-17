from typing import Optional

from catan.bots.mcts import MCTSNode
from catan.core.models.player import Color


def _get_action_string(action_obj: Optional[object]) -> str:
    """Helper to get a string representation of an action."""
    if not action_obj:
        return "N/A (Root)"

    # Attempt to get action type name
    action_type_name = "UnknownType"
    action_type_attr = getattr(action_obj, "action_type", None)
    if action_type_attr is not None:
        action_type_name = getattr(action_type_attr, "name", str(action_type_attr))

    # Attempt to get action value string
    action_value_str = ""
    action_value = getattr(action_obj, "value", None)
    if action_value is not None:
        action_value_str = f"({action_value})"

    # Attempt to get player color string for the action
    player_color_str = ""
    action_color_attr = getattr(action_obj, "color", None)
    if action_color_attr is not None:
        player_color_name = getattr(action_color_attr, "name", str(action_color_attr))
        player_color_str = f"P({player_color_name}): "

    return f"{player_color_str}{action_type_name}{action_value_str}"


def _print_mcts_node_recursive(
    node: MCTSNode,
    prefix: str,
    is_last_child: bool,
    max_depth: Optional[int],
    current_depth: int,
    mcts_agent_color: Color,  # The color of the MCTS agent running the search
):
    """
    Recursively prints a subtree for the MCTS.
    node: The current MCTSNode to print.
    prefix: The string prefix for drawing tree lines.
    is_last_child: True if this node is the last among its siblings.
    max_depth: Maximum depth of descendants to print (relative to the initial call's root).
    current_depth: The current depth of this node (relative to the initial call's root).
    mcts_agent_color: The color of the player for whom MCTS is being run.
    """

    # 1. Construct and print current node's information line
    line = prefix
    line += "└── " if is_last_child else "├── "

    action_str = _get_action_string(node.action)

    ucb_score_val = node.ucb1_score()  # Assumes MCTSNode has this method
    ucb_score_str = ucb_score_val

    # Wins/visits are from the perspective of mcts_agent_color
    mcts_agent_color_name = getattr(mcts_agent_color, "name", str(mcts_agent_color))
    line += f"Act: {action_str} [W/V: {node.wins}/{node.visits} for P({mcts_agent_color_name}), UCB1: {ucb_score_str}]"

    # Current player in the game state of *this* node
    current_turn_player_name = "N/A"
    if (
        node.game
        and hasattr(node.game, "state")
        and node.game.state
        and hasattr(node.game.state, "current_player_color")
        and node.game.state.current_player_color
    ):
        current_turn_player_name = getattr(
            node.game.state.current_player_color,
            "name",
            str(node.game.state.current_player_color),
        )
    line += f" (Turn: P({current_turn_player_name}))"

    if node.is_terminal_node():  # Assumes MCTSNode has this method
        line += " (Terminal)"
    # Check if it's a leaf in the MCTS tree (no children explored yet or fully expanded without children)
    elif not node.children:
        if node.is_fully_expanded():  # Assumes MCTSNode has this method
            line += " (Leaf - Fully Expanded)"
        else:
            line += " (Leaf - Not Fully Expanded)"

    print(line)

    # 2. Check depth before recursing for children
    if max_depth is not None and current_depth >= max_depth:
        if node.children:
            children_prefix_for_dots = prefix + ("    " if is_last_child else "│   ")
            # Indicate truncation if there are children not being shown
            print(
                children_prefix_for_dots
                + ("└── " if len(node.children) == 1 and is_last_child else "├── ")
                + "... (depth limit reached)"
            )
        return

    # 3. Recursively call for children
    children_prefix = prefix + ("    " if is_last_child else "│   ")
    for i, child_node in enumerate(node.children):
        is_last = i == len(node.children) - 1
        _print_mcts_node_recursive(
            child_node,
            children_prefix,
            is_last,
            max_depth,
            current_depth + 1,
            mcts_agent_color,
        )


def pretty_print_mcts_tree(root_node: MCTSNode, max_depth: Optional[int] = 3):
    """
    Pretty prints the MCTS tree starting from the given root_node.
    root_node: The root MCTSNode of the tree to print.
    max_depth: Levels of descendants to print.
               0 means print only the root_node itself.
               1 means root_node and its direct children.
               N means root_node and N levels of its descendants.
               None means print all levels.
    """
    if not root_node:
        print("MCTS tree is empty (root_node is None).")
        return

    mcts_agent_color = root_node.color  # The perspective for W/V stats
    mcts_agent_color_name = getattr(mcts_agent_color, "name", str(mcts_agent_color))

    # Print information for the root node
    root_info = f"MCTS Root (P({mcts_agent_color_name}) perspective) "
    root_info += f"[Total W/V: {root_node.wins}/{root_node.visits}]"

    # The root_node itself doesn't have an action that *led* to it from a parent in this context,
    # but if it's a subtree, node.action might be set.
    # For the absolute root of an MCTS search, node.action is typically None.
    if root_node.action:
        root_info += f" (Reached via Action: {_get_action_string(root_node.action)})"

    current_turn_player_name = "N/A"
    if (
        root_node.game
        and hasattr(root_node.game, "state")
        and root_node.game.state
        and hasattr(root_node.game.state, "current_player_color")
        and root_node.game.state.current_player_color
    ):
        current_turn_player_name = getattr(
            root_node.game.state.current_player_color,
            "name",
            str(root_node.game.state.current_player_color),
        )
    root_info += f" (Current Turn: P({current_turn_player_name}))"

    if root_node.is_terminal_node():
        root_info += " (Terminal State)"

    print(root_info)

    if (
        max_depth is not None and max_depth < 0
    ):  # Should not happen with default, but good check
        print("Invalid max_depth (< 0). Not printing children.")
        return

    if max_depth == 0:  # Only print root if max_depth is 0
        if root_node.children:
            print("└── ... (children not printed, max_depth = 0)")
        return

    # Recursively print for children
    # Direct children are at current_depth = 1 relative to this root node.
    for i, child_node in enumerate(root_node.children):
        is_last = i == len(root_node.children) - 1
        _print_mcts_node_recursive(
            child_node,
            prefix="",  # Initial prefix for children of the root
            is_last_child=is_last,
            max_depth=max_depth,
            current_depth=1,
            mcts_agent_color=mcts_agent_color,
        )
