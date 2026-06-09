GRID_SIZE = 10
COLS = "ABCDEFGHIJ"
ROWS = list(range(1, GRID_SIZE + 1))

SHIPS = [
    ("Carrier",    5),
    ("Battleship", 4),
    ("Cruiser",    3),
    ("Submarine",  3),
    ("Destroyer",  2),
]

# Cell states
EMPTY   = "."
SHIP    = "S"   # hidden from opponent
HIT     = "X"
MISS    = "O"
SUNK    = "#"

# CLI colours (fall back gracefully if unsupported)
R  = "\033[91m"   # red
G  = "\033[92m"   # green
Y  = "\033[93m"   # yellow
B  = "\033[94m"   # blue
DIM = "\033[2m"
RST = "\033[0m"
