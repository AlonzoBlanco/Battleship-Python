# Battleship AI Simulation Engine

A Python implementation of Battleship with a playable Pygame interface and AI-vs-AI simulation support.

The project includes a standard 10x10 Battleship board, random ship placement, manual player ship placement, and two AI strategies: a basic random shooter and a more structured Hunter AI. It can be used either as a small game against the AI or as a way to compare AI behavior over multiple simulated matches.

## Features

* **Player vs AI mode**
  Play Battleship against an AI opponent using the Pygame interface. The player manually places ships on the board before the match begins.

* **AI vs AI simulation**
  Run multiple matches between two AI players and compare their results.

* **Two AI strategies**

  * `RandomAI`: chooses unplayed cells at random.
  * `HunterAI`: starts with a checkerboard search pattern, then switches to targeted shots after finding a hit.

* **Match statistics**
  After running AI simulations, the program tracks results such as:

  * number of wins per player
  * average turns per game
  * hit accuracy
  * exploration vs. targeted shots

* **Graph generation**
  Simulation results can be visualized with Matplotlib and Seaborn charts.

## Project Structure

```text
.
├── app.py              # Main Pygame application and simulation flow
├── models/
│   ├── board.py        # Board logic, ship placement, and shot handling
│   ├── constants.py    # Grid size, ships, and cell states
│   └── player.py       # Human player, Random AI, and Hunter AI classes
├── requirements.txt
└── README.md
```

## How It Works

The game is built around a simple state-based flow:

1. **Menu**
   Choose the game mode, player names, AI types, and number of simulation matches.

2. **Placement**
   In Player vs AI mode, the player places their ships manually on the board. Press `R` to rotate the current ship.

3. **Gameplay**
   Players take turns firing at the opponent’s board. Hits, misses, and sunk ships are updated on the grid.

4. **Simulation Results**
   In AI vs AI mode, the program can run many matches without rendering every move. After the simulation, it shows win totals and average game statistics.

## AI Behavior

### RandomAI

The `RandomAI` strategy is intentionally simple. It selects a random cell that has not been shot before. This makes it useful as a baseline for comparing other strategies.

### HunterAI

The `HunterAI` uses a more organized approach:

1. It searches the board using a checkerboard pattern.
2. When it hits a ship, it switches into target mode.
3. It checks nearby cells to continue damaging the same ship.
4. Once it detects the direction of the ship, it focuses shots along that axis.
5. After sinking a ship, it returns to search mode.

This does not guarantee perfect play, but it reduces many wasted shots compared to fully random guessing.

## Setup

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

The main libraries used are:

```text
pygame
numpy
matplotlib
seaborn
```

## Running the Project

Run the main application with:

```bash
python app.py
```

From the menu, you can choose between:

* `PvAI`: Player vs AI
* `AIvAI`: AI vs AI simulation

For AI simulations, you can also set how many matches should be played.

## Controls

During ship placement:

```text
Left Click   Place current ship
R            Rotate current ship
```

During gameplay:

```text
Left Click   Fire at a cell on the enemy board
```

## Notes

Simulation results can vary because ship placement and some AI decisions use randomness. For more consistent testing, a random seed could be added in the future.

The current project focuses on gameplay logic, AI behavior, and basic statistical comparison rather than being a fully finished commercial game.
