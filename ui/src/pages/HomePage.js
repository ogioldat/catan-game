import React, { useState } from "react";
import { useHistory } from "react-router-dom";
import { Button } from "@material-ui/core";
import Loader from "react-loader-spinner";
import { createGame } from "../utils/apiClient";

import "./HomePage.scss";

const GameMode = Object.freeze({
  RANDOM_VS_RANDOM: "RANDOM_VS_RANDOM",
  MCTS_VS_RANDOM: "MCTS_VS_RANDOM",
});

function getPlayers(gameMode, numPlayers) {
  switch (gameMode) {
    case GameMode.RANDOM_VS_RANDOM:
      return ["RANDOM", "RANDOM"];
    case GameMode.MCTS_VS_RANDOM:
      return ["MCTS", "RANDOM"];
    default:
      throw new Error("Invalid Game Mode");
  }
}

export default function HomePage() {
  const [loading, setLoading] = useState(false);
  const [numPlayers, setNumPlayers] = useState(2);
  const history = useHistory();

  const handleCreateGame = async (gameMode) => {
    setLoading(true);
    const players = getPlayers(gameMode, numPlayers);
    const gameId = await createGame(players);
    setLoading(false);
    history.push("/games/" + gameId);
  };

  return (
    <div className="home-page">
      <h1 className="logo">The Settlers of Catan</h1>
      <h2>Multi-Agent Playout</h2>

      <div className="switchable">
        {!loading ? (
          <>
            <Button
              variant="contained"
              color="primary"
              onClick={() => handleCreateGame(GameMode.RANDOM_VS_RANDOM)}
            >
              Random vs Random
            </Button>
            <Button
              variant="contained"
              color="primary"
              onClick={() => handleCreateGame(GameMode.MCTS_VS_RANDOM)}
            >
              MCTS vs Random
            </Button>
          </>
        ) : (
          <Loader
            className="loader"
            type="Grid"
            color="#ffffff"
            height={60}
            width={60}
          />
        )}
      </div>
    </div>
  );
}
