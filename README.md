# Catan Game

## Running the game

1. Setup venv or conda env.
2. Install deps `pip install -r requirements.txt`
3. Active dev dirs
   - `/catan/bots` -- create new AI bots,
   - `/catan/analysis` -- analyze playout stats and bot strategies.
4. Preview playouts in UI
   - Run script `run_server`
   - Run script `run_ui`

## Development plan

- [ ] AI player agents
  - [ ] Find a way to evaluate agent performance
    - [ ] Measure win rate in multi-agent playouts
  - [ ] MCTS Player
    - [ ] Initial implementation
    - [ ] Optimal MCTS player with action pruning
  - [ ] RL
    - [ ] Implement custom Gymnasium environment for Catan
    - [ ] Decide which RL algorithms we might need (A2C, PPO, DQN, other...)
    - [ ]
- [ ] Game UI
  - [ ] Show agentic playouts visible in UI

### Resources

- <https://github.com/higgsfield/RL-Adventure/tree/master>

### Open questions

- Temporal Difference over Monte Carlo methods?
- What is the action space?
- How should we architect the neural network?
- Which RL algo should we use?
- On-policy vs Off-policy methods?
- When (if so) can we utilize self-play?
- NN
  - Input features for NN?
  - How to model randomness?
  - Is RNN suitable?
  - How to model agent strategies?
  - How to model dueling?

## Core game logic credit

This repo uses `catanator`'s modules for catan core game logic
