import React, { useCallback, useContext, useEffect, useState } from "react";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import clsx from "clsx";
import memoize from "fast-memoize";

import useWindowSize from "../utils/useWindowSize";
import { SQRT3 } from "../utils/coordinates";
import Tile from "./Tile";
import Node from "./Node";
import Edge from "./Edge";
import Robber from "./Robber";

import "./Board.scss";
import { store } from "../store";
import { isPlayersTurn } from "../utils/stateUtils";
import { postAction } from "../utils/apiClient";
import { useParams } from "react-router";
import ACTIONS from "../actions";

/**
 * This uses the formulas: W = SQRT3 * size and H = 2 * size.
 * Math comes from https://www.redblobgames.com/grids/hexagons/.
 */
function computeDefaultSize(divWidth, divHeight) {
  const numLevels = 6; // 3 rings + 1/2 a tile for the outer water ring
  // divHeight = numLevels * (3h/4) + (h/4), implies:
  const maxSizeThatRespectsHeight = (4 * divHeight) / (3 * numLevels + 1) / 2;
  const correspondingWidth = SQRT3 * maxSizeThatRespectsHeight;
  let size;
  if (numLevels * correspondingWidth < divWidth) {
    // thus complete board would fit if we pick size based on height (height is limiting factor)
    size = maxSizeThatRespectsHeight;
  } else {
    // we'll have to decide size based on width.
    const maxSizeThatRespectsWidth = divWidth / numLevels / SQRT3;
    size = maxSizeThatRespectsWidth;
  }
  return size;
}

/**
 * Returns object representing actions to be taken if click on node.
 * @returns {3 => ["BLUE", "BUILD_CITY", 3], ...}
 */
function buildNodeActions(state) {
  if (!isPlayersTurn(state.gameState)) {
    return {};
  }

  const nodeActions = {};

  const buildInitialSettlementActions = state.gameState.current_playable_actions.filter(
    (action) =>
      action[1] === "BUILD_FIRST_SETTLEMENT" ||
      action[1] === "BUILD_SECOND_SETTLEMENT"
  );
  const inInitialBuildPhase = buildInitialSettlementActions.length > 0;
  if (inInitialBuildPhase) {
    buildInitialSettlementActions.forEach((action) => {
      nodeActions[action[2]] = action;
    });
  } else if (state.isBuildingSettlement) {
    state.gameState.current_playable_actions
      .filter((action) => action[1] === "BUILD_SETTLEMENT")
      .forEach((action) => {
        nodeActions[action[2]] = action;
      });
  } else if (state.isBuildingCity) {
    state.gameState.current_playable_actions
      .filter((action) => action[1] === "BUILD_CITY")
      .forEach((action) => {
        nodeActions[action[2]] = action;
      });
  }
  return nodeActions;
}

export default function ZoomableBoard() {
  const { gameId } = useParams();
  const { state, dispatch } = useContext(store);
  const { width, height } = useWindowSize();
  const [show, setShow] = useState(false);

  const buildOnNodeClick = useCallback(
    memoize((id, action) => async () => {
      console.log("Clicked Node ", id);
      if (action) {
        console.log("Firing", action);
        const gameState = await postAction(gameId, action);
        dispatch({ type: ACTIONS.SET_GAME_STATE, data: gameState });
      }
    }),
    []
  );

  // TODO: Keep in sync with CSS
  const containerHeight = height - 144 - 38 - 40;
  const center = [width / 2, containerHeight / 2];
  const size = computeDefaultSize(width, containerHeight);

  const nodeActions = buildNodeActions(state);

  let board;
  if (size) {
    const tiles = state.gameState.tiles.map(({ coordinate, tile }) => (
      <Tile
        key={coordinate}
        center={center}
        coordinate={coordinate}
        tile={tile}
        size={size}
      />
    ));
    const nodes = Object.values(
      state.gameState.nodes
    ).map(({ color, building, direction, tile_coordinate, id }) => (
      <Node
        key={id}
        center={center}
        size={size}
        coordinate={tile_coordinate}
        direction={direction}
        building={building}
        color={color}
        flashing={id in nodeActions}
        onClick={buildOnNodeClick(id, nodeActions[id])}
      />
    ));
    const edges = Object.values(
      state.gameState.edges
    ).map(({ color, direction, tile_coordinate, id }) => (
      <Edge
        id={id}
        key={id}
        center={center}
        size={size}
        coordinate={tile_coordinate}
        direction={direction}
        color={color}
      />
    ));
    board = (
      <div className={clsx("board", { show })}>
        {tiles}
        {edges}
        {nodes}
        <Robber
          center={center}
          size={size}
          coordinate={state.gameState.robber_coordinate}
        />
      </div>
    );
  }

  useEffect(() => {
    setTimeout(() => {
      setShow(true);
    }, 300);
  }, []);

  return (
    <TransformWrapper
      options={{
        limitToBounds: true,
      }}
    >
      {({
        zoomIn,
        zoomOut,
        resetTransform,
        positionX,
        positionY,
        scale,
        previousScale,
      }) => (
        <React.Fragment>
          <div className="board-container">
            <TransformComponent>{board}</TransformComponent>
          </div>
        </React.Fragment>
      )}
    </TransformWrapper>
  );
}
