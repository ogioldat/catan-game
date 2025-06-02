from enum import Enum

import numpy as np
from catan.core.models.enums import (
    BRICK,
    ORE,
    SHEEP,
    WHEAT,
    WOOD,
    Action as CatanAction,
    ActionType,
)
from catan.core.models.player import Color


class TileEncoding(Enum):
    WOOD = WOOD
    BRICK = BRICK
    SHEEP = SHEEP
    WHEAT = WHEAT
    ORE = ORE
    EMPTY = "EMPTY"
    HAS_ROBBER = "HAS_ROBBER"


class NodeBuildingEncoding(Enum):
    SETTLEMENT = "SETTLEMENT"
    CITY = "CITY"
    NONE = "NONE"


class NodePlayerEncoding(Enum):
    RED = Color.RED
    BLUE = Color.BLUE
    ORANGE = Color.ORANGE
    WHITE = Color.WHITE


class TileEncoder:
    # def _node_block(self):

    def __init__(self) -> None:
        self.node_labels = (
            NodeBuildingEncoding.SETTLEMENT,
            NodeBuildingEncoding.CITY,
            NodeBuildingEncoding.NONE,
            NodePlayerEncoding.RED,
            NodePlayerEncoding.BLUE,
            NodePlayerEncoding.ORANGE,
            NodePlayerEncoding.WHITE,
        )
        self.tile_value_labels = range(2, 13)
        self.tile_labels = (
            TileEncoding.WOOD,
            TileEncoding.BRICK,
            TileEncoding.SHEEP,
            TileEncoding.WHEAT,
            TileEncoding.ORE,
            TileEncoding.EMPTY,
            TileEncoding.HAS_ROBBER,
            *self.tile_value_labels,
            *6 * self.node_labels,
        )

        self.node_encoding_start = self.tile_labels.index(self.node_labels[0])
        self.size = len(self.tile_labels)

    def get_initial_encoding(self, value: int | None, resource):
        encoding = self.empty_encoding()

        resource_idx = self.tile_labels.index(resource)
        assert resource_idx is not None

        if value is not None:
            value_idx = self.tile_labels.index(value)
            encoding[value_idx] = 1

        encoding[resource_idx] = 1

        return encoding

    def empty_encoding(self):
        return np.zeros(self.size, dtype=np.int8)

    def encode_node(
        self,
        encoding: np.ndarray,
        player_encoding: NodePlayerEncoding,
        building_encoding: NodeBuildingEncoding,
        node_idx,
    ):
        assert node_idx >= 0 and node_idx < 6

        relative_idx = self.node_encoding_start + len(self.node_labels) * node_idx
        building_relative_idx = self.node_labels.index(building_encoding)
        player_relative_idx = self.node_labels.index(
            NodePlayerEncoding[player_encoding]
        )

        enc = encoding.copy()

        enc[relative_idx + building_relative_idx] = 1
        enc[relative_idx + player_relative_idx] = 1

        return enc

    def encode(self, game):
        pass
