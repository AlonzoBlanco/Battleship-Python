import random
from models.constants import GRID_SIZE, COLS, ROWS, SHIPS, EMPTY, SHIP, HIT, MISS, SUNK, R, G, DIM, RST

class Board:
    """Represents one player's 10x10 grid."""

    def __init__(self, owner_name: str):
        self.owner = owner_name
        self.grid: list[list[str]] = [[EMPTY]*GRID_SIZE for _ in range(GRID_SIZE)]
        self.ships: list[dict] = []          # placed ship records
        self.shots_received: set[tuple] = set()

    # ── Coordinate helpers ──────────────────

    @staticmethod
    def parse(coord: str) -> tuple[int, int]:
        """Parse 'B5' → (col_idx, row_idx). Raises ValueError on bad input."""
        coord = coord.strip().upper()
        if len(coord) < 2:
            raise ValueError(f"Invalid coordinate: {coord!r}")
        col_ch = coord[0]
        row_s  = coord[1:]
        if col_ch not in COLS:
            raise ValueError(f"Column must be A-J, got {col_ch!r}")
        try:
            row = int(row_s)
        except ValueError:
            raise ValueError(f"Row must be 1-10, got {row_s!r}")
        if row not in ROWS:
            raise ValueError(f"Row must be 1-10, got {row}")
        return COLS.index(col_ch), row - 1

    @staticmethod
    def format(col: int, row: int) -> str:
        return f"{COLS[col]}{row+1}"

    # ── Ship placement ──────────────────────

    def can_place(self, col: int, row: int, length: int, horizontal: bool) -> bool:
        for i in range(length):
            c = col + (i if horizontal else 0)
            r = row + (0 if horizontal else i)
            if not (0 <= c < GRID_SIZE and 0 <= r < GRID_SIZE):
                return False
            if self.grid[r][c] != EMPTY:
                return False
        return True

    def place_ship(self, name: str, col: int, row: int, length: int, horizontal: bool):
        cells = []
        for i in range(length):
            c = col + (i if horizontal else 0)
            r = row + (0 if horizontal else i)
            self.grid[r][c] = SHIP
            cells.append((c, r))
        self.ships.append({"name": name, "length": length,
                            "cells": cells, "hits": set(), "sunk": False})

    def place_ship_random(self, name: str, length: int):
        while True:
            h   = random.choice([True, False])
            col = random.randint(0, GRID_SIZE - 1)
            row = random.randint(0, GRID_SIZE - 1)
            if self.can_place(col, row, length, h):
                self.place_ship(name, col, row, length, h)
                return

    def place_all_random(self):
        for name, length in SHIPS:
            self.place_ship_random(name, length)

    # ── Receiving a shot ────────────────────

    def receive_shot(self, col: int, row: int) -> str:
        """Process an incoming shot. Returns 'hit', 'miss', or 'sunk:<ShipName>'."""
        if (col, row) in self.shots_received:
            return "duplicate"
        self.shots_received.add((col, row))

        cell = self.grid[row][col]
        if cell in (EMPTY, MISS):
            self.grid[row][col] = MISS
            return "miss"

        if cell in (SHIP, HIT):
            self.grid[row][col] = HIT
            for ship in self.ships:
                if (col, row) in ship["cells"]:
                    ship["hits"].add((col, row))
                    if ship["hits"] == set(ship["cells"]):
                        ship["sunk"] = True
                        # mark all cells as SUNK
                        for c2, r2 in ship["cells"]:
                            self.grid[r2][c2] = SUNK
                        return f"sunk:{ship['name']}"
                    return "hit"
        return "miss"   # fallback

    def all_sunk(self) -> bool:
        return all(s["sunk"] for s in self.ships)

    # ── Display ─────────────────────────────

    def render(self, hide_ships: bool = False) -> str:
        """Return a string representation of the board."""
        header  = f"  {'  '.join(COLS)}"
        lines   = [header]
        for r in range(GRID_SIZE):
            row_label = f"{r+1:>2}"
            cells = []
            for c in range(GRID_SIZE):
                ch = self.grid[r][c]
                if hide_ships and ch == SHIP:
                    ch = EMPTY
                cells.append(self._colour(ch))
            lines.append(f"{row_label} {' '.join(cells)}")
        return "\n".join(lines)

    @staticmethod
    def _colour(ch: str) -> str:
        if ch == HIT:  return f"{R}{ch}{RST}"
        if ch == SUNK: return f"{R}{ch}{RST}"
        if ch == MISS: return f"{DIM}{ch}{RST}"
        if ch == SHIP: return f"{G}{ch}{RST}"
        return ch
