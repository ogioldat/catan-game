from collections import defaultdict
from enum import Enum
from catan.core.models.enums import Action, ActionType


class CatanRewards(Enum):
    BUILT_SETTLEMENT = 10
    BUILT_CITY = 15
    OWNS_LONGEST_ROAD_TITLE = 20
    OWNS_LARGEST_ARMY_TITLE = 20
    OWNS_DEV_CARD_VP = 10

    # Activities leading to future rewards
    BUILT_ROAD = 1
    BOUGHT_DEV_CARD = 1
    ACTIVATED_PORT = 3
    MOVE_ROBBER = 0.1

    # Penalties
    LOST_LONGEST_ROAD_TITLE = -30
    LOST_LARGEST_ARMY_TITLE = -30
    END_TURN = -0.2

    # Ultimate victory
    GAME_WON = 100


ACTION_REWARDS = defaultdict(
    lambda: 0,
    {
        ActionType.MOVE_ROBBER: CatanRewards.BUILT_ROAD.MOVE_ROBBER.value,
        ActionType.BUILD_ROAD: CatanRewards.BUILT_ROAD.value,
        ActionType.BUILD_SETTLEMENT: CatanRewards.BUILT_SETTLEMENT.value,
        ActionType.BUILD_CITY: CatanRewards.BUILT_CITY.value,
        ActionType.BUY_DEVELOPMENT_CARD: CatanRewards.BOUGHT_DEV_CARD.value,
        ActionType.END_TURN: CatanRewards.END_TURN.value,
    },
)


def action_to_reward(catan_action: Action) -> float:
    reward = ACTION_REWARDS.get(catan_action.action_type)

    return reward
