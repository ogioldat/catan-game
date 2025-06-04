import React, { useState, useContext } from "react";
import cn from "classnames";
import SwipeableDrawer from "@material-ui/core/SwipeableDrawer";
import Divider from "@material-ui/core/Divider";
import Drawer from "@material-ui/core/Drawer";
import { Hidden } from "@material-ui/core";

import PlayerStateBox from "../components/PlayerStateBox";
import { humanizeAction } from "../components/Prompt";
import { store } from "../store";
import ACTIONS from "../actions";
import { playerKey } from "../utils/stateUtils";

import "./LeftDrawer.scss";

function PlayersInfo({ gameState }) {
  const playerSections = gameState.colors.map((color) => {
    const key = playerKey(gameState, color);
    return (
      <React.Fragment key={color}>
        <PlayerStateBox
          playerState={gameState.player_state}
          playerKey={key}
          color={color}
        />
        <Divider />
      </React.Fragment>
    );
  });

  return (
    <>
      {playerSections}
    </>
  );
}

export default function LeftDrawer() {
  const { state, dispatch } = useContext(store);

  return (
    <>
      <Hidden implementation="css">
        <Drawer className="left-drawer" anchor="left" variant="permanent" open>
          <PlayersInfo gameState={state.gameState} />
        </Drawer>
      </Hidden>

      <Hidden implementation="css">
        <Drawer className="left-drawer" anchor="right" variant="permanent" open>
        <h2>Event Log</h2>
        <div className="log">
          {state.gameState.actions
            .reverse()
            .map((action, i) =>  {
              return (
                <>
                  <div key={i} style={{fontWeight: "bold"}} className={cn("action foreground", action[0])}>
                    {humanizeAction(state.gameState, action)}
                  </div>
  
                </>
                )
              }
            )}
        </div>
        </Drawer>
      </Hidden>
    </>
  );
}
