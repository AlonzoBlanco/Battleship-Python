import random
import time
from abc import ABC, abstractmethod
from typing import Optional
from models.board import Board
from models.constants import GRID_SIZE, MISS, HIT, SUNK, SHIPS

class Player(ABC):
    """Abstract base – subclass for Human or any AI agent."""

    def __init__(self, name: str):
        self.name  = name
        self.board = Board(name)          # own ships live here
        self.tracking_grid = Board(f"{name}_track")  # shots fired at opponent
        
        # Statistics
        self.shots_fired = 0
        self.hits_landed = 0
        self.exploration_shots = 0
        self.exploitation_shots = 0
        self.decision_time_total = 0.0

    @abstractmethod
    def place_ships(self):
        """Populate self.board with ships."""
        ...

    @abstractmethod
    def choose_shot(self) -> tuple[int, int]:
        """Return (col, row) to fire at. Must not already have been shot."""
        ...

    def record_shot_result(self, col: int, row: int, result: str):
        """Engine calls this after the shot so the player can update its tracking."""
        if result == "miss":
            self.tracking_grid.grid[row][col] = MISS
        elif result.startswith("sunk"):
            self.tracking_grid.grid[row][col] = SUNK
            self.hits_landed += 1
        else:
            self.tracking_grid.grid[row][col] = HIT
            self.hits_landed += 1

class HumanPlayer(Player):
    """
    Human player class.
    All interactions (placement, choosing shots) are handled externally by the GUI.
    """
    def place_ships(self):
        pass  # Handled by GUI

    def choose_shot(self) -> tuple[int, int]:
        raise NotImplementedError("Shot selection is handled via Pygame events in the GUI.")

class RandomAI(Player):
    """Fires at completely random, un-shot cells."""

    def place_ships(self):
        self.board.place_all_random()

    def choose_shot(self) -> tuple[int, int]:
        start_time = time.perf_counter()
        while True:
            col = random.randint(0, GRID_SIZE - 1)
            row = random.randint(0, GRID_SIZE - 1)
            if (col, row) not in self.tracking_grid.shots_received:
                self.tracking_grid.shots_received.add((col, row))
                self.shots_fired += 1
                self.exploration_shots += 1
                self.decision_time_total += time.perf_counter() - start_time
                return col, row

class HunterAI(Player):
    """
    Advanced Hunt/Target AI:
    - In HUNT mode fires in a parity checkerboard pattern to maximise coverage.
    - When a hit lands, switches to TARGET mode and probes adjacent cells.
    - If a second hit lands on the same ship, it determines the axis (horizontal/vertical)
      and only probes along that axis.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self._mode = "hunt"
        self._hit_stack : list[tuple[int,int]] = []   # cells to probe
        self._first_hit : Optional[tuple[int,int]] = None
        self._last_hit  : Optional[tuple[int,int]] = None
        self._axis      : Optional[str] = None # 'H' or 'V'
        self._hunt_cells: list[tuple[int,int]] = self._checkerboard()
        self._current_ship_hits: list[tuple[int,int]] = []

    @staticmethod
    def _checkerboard() -> list[tuple[int,int]]:
        # Using a parity of 2 since the smallest ship is length 2 (Destroyer)
        cells = [(c, r) for r in range(GRID_SIZE)
                          for c in range(GRID_SIZE)
                          if (c + r) % 2 == 0]
        random.shuffle(cells)
        rest  = [(c, r) for r in range(GRID_SIZE)
                          for c in range(GRID_SIZE)
                          if (c + r) % 2 == 1]
        random.shuffle(rest)
        return cells + rest

    def place_ships(self):
        self.board.place_all_random()

    def _get_adjacent(self, col, row, axis=None):
        adj = []
        if axis in (None, 'V'):
            adj.extend([(col, row-1), (col, row+1)])
        if axis in (None, 'H'):
            adj.extend([(col-1, row), (col+1, row)])
        return [(c, r) for c, r in adj if 0 <= c < GRID_SIZE and 0 <= r < GRID_SIZE]

    def choose_shot(self) -> tuple[int, int]:
        start_time = time.perf_counter()
        
        while True:
            is_exploit = False
            if self._mode == "target" and self._hit_stack:
                col, row = self._hit_stack.pop()
                is_exploit = True
            else:
                self._mode = "hunt"
                if not self._hunt_cells:
                    # Fallback if hunt cells empty (shouldn't happen)
                    col, row = random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)
                else:
                    col, row = self._hunt_cells.pop(0)

            if (col, row) not in self.tracking_grid.shots_received:
                self.tracking_grid.shots_received.add((col, row))
                self.shots_fired += 1
                if is_exploit:
                    self.exploitation_shots += 1
                else:
                    self.exploration_shots += 1
                
                self.decision_time_total += time.perf_counter() - start_time
                return col, row

    def record_shot_result(self, col: int, row: int, result: str):
        super().record_shot_result(col, row, result)
        
        if result == "miss":
            pass
        elif result.startswith("sunk"):
            self._mode = "hunt"
            self._hit_stack.clear()
            self._first_hit = None
            self._last_hit = None
            self._axis = None
            self._current_ship_hits.clear()
            
        else:   # hit
            self._current_ship_hits.append((col, row))
            if self._mode == "hunt":
                self._mode = "target"
                self._first_hit = (col, row)
                self._axis = None
                
                # Add all adjacent cells to stack
                for nc, nr in self._get_adjacent(col, row):
                    if (nc, nr) not in self.tracking_grid.shots_received:
                        self._hit_stack.append((nc, nr))
            
            elif self._mode == "target":
                # We got another hit! Can we determine axis?
                if not self._axis and len(self._current_ship_hits) >= 2:
                    c1, r1 = self._current_ship_hits[0]
                    c2, r2 = self._current_ship_hits[-1]
                    if c1 == c2:
                        self._axis = 'V'
                    elif r1 == r2:
                        self._axis = 'H'
                
                self._last_hit = (col, row)
                
                # Filter hit stack to only include the determined axis
                if self._axis:
                    valid_stack = []
                    for c, r in self._hit_stack:
                        if self._axis == 'V' and c == self._first_hit[0]:
                            valid_stack.append((c, r))
                        elif self._axis == 'H' and r == self._first_hit[1]:
                            valid_stack.append((c, r))
                    self._hit_stack = valid_stack
                
                # Add new adjacent cells along the axis
                for nc, nr in self._get_adjacent(col, row, self._axis):
                    if (nc, nr) not in self.tracking_grid.shots_received:
                        self._hit_stack.append((nc, nr))
