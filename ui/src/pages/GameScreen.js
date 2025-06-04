import React, { useEffect, useState, useContext } from "react";
import { useParams } from "react-router-dom";
import PropTypes from "prop-types";
import Loader from "react-loader-spinner";
import { useSnackbar } from "notistack";

import ZoomableBoard from "./ZoomableBoard";

import "react-loader-spinner/dist/loader/css/react-spinner-loader.css";
import "./GameScreen.scss";
import LeftDrawer from "../components/LeftDrawer";
import { store } from "../store";
import ACTIONS from "../actions";
import { getState, postAction } from "../utils/apiClient";
import { dispatchSnackbar } from "../components/Snackbar";
import { getHumanColor } from "../utils/stateUtils";

const ROBOT_THINKING_TIME = 300;

function GameScreen({ replayMode }) {
  const { gameId, stateIndex } = useParams();
  const { state, dispatch } = useContext(store);
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();

  // Load game state
  useEffect(() => {
    if (!gameId) {
      return;
    }

    (async () => {
      const gameState = await getState(gameId, stateIndex);
      dispatch({ type: ACTIONS.SET_GAME_STATE, data: gameState });
    })();
  }, [gameId, stateIndex, dispatch]);

  // Maybe kick off next query?
  useEffect(() => {
    if (!state.gameState || replayMode) {
      return;
    }
    if (
      state.gameState.bot_colors.includes(state.gameState.current_color) &&
      !state.gameState.winning_color
    ) {
      // Make bot click next action.
      (async () => {
        const start = new Date();
        const gameState = await postAction(gameId);
        const requestTime = new Date() - start;
        setTimeout(() => {
          // simulate thinking
          dispatch({ type: ACTIONS.SET_GAME_STATE, data: gameState });
          if (getHumanColor(gameState)) {
            dispatchSnackbar(enqueueSnackbar, closeSnackbar, gameState);
          }
        }, ROBOT_THINKING_TIME - requestTime);
      })();
    }
  }, [
    gameId,
    replayMode,
    state.gameState,
    dispatch,
    enqueueSnackbar,
    closeSnackbar,
  ]);

  if (!state.gameState) {
    return (
      <main>
        <Loader
          className="loader"
          type="Oval"
          color="#000000"
          height={100}
          width={100}
        />
      </main>
    );
  }

  const clrsMap = {
    BLUE: '#2b6ed9',
    RED: '#c83d3a',
    ORANGE: '#ffa500',
    VIOLET: '#8F00FF'
  }


  return (
    <main>
        <h1 className="logo">
          {
            state.gameState.players.map((plr, idx) => 
              <span 
                style={{color: clrsMap[plr.color]}} 
                key={plr.color}>
                  
                  <span style={{color: "black"}}>
                  { idx > 0 ? " vs " : ""}
                  </span>
                  
                  {plr.kind}
              </span>
            )
          }
        </h1>

      <div style={{margin: "0 auto", fontSize: 25 }}>
        {
            state.gameState.winning_color &&
            <span style={{fontWeight:"bold", color: clrsMap[state.gameState.players.find(p => p.color == state.gameState.winning_color).color]}}>
              {state.gameState.players.find(p => p.color == state.gameState.winning_color).kind}  
            </span> 
          } wins 👑
      </div>

      <ZoomableBoard replayMode={replayMode} />
      <LeftDrawer />
    </main>
  );
}

GameScreen.propTypes = {
  /**
   * Injected by the documentation to work in an iframe.
   * You won't need it on your project.
   */
  window: PropTypes.func,
};

export default GameScreen;
