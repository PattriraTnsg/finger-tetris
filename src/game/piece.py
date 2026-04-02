# """
# piece.py — Tetrominoes definition + SRS rotation system

# Each piece stores:
# - shape matrices for all 4 rotation states
# - current rotation index
# - color id (1-7, matches renderer palette)

# Rotation uses SRS (Super Rotation System) wall-kick data so pieces
# behave like official Tetris guidelines.
# """

from __future__ import annotations
from dataclasses import dataclass, field
from typing import ClassVar
import copy

# ---------------------------------------------------------------------------
# Shape matrices  (each is a list of (row, col) offsets from top-left 0,0)
# ---------------------------------------------------------------------------
# Stored as 4 rotation states: [state0, state1, state2, state3]
# Using standard Tetris guideline colours (color_id 1-7):
#   1=I (cyan), 2=O (yellow), 3=T (purple), 4=S (green),
#   5=Z (red), 6=J (blue), 7=L (orange)

_SHAPES: dict[str, list[list[tuple[int, int]]]] = {
    "I": [
        [(0,0),(0,1),(0,2),(0,3)],
        [(0,2),(1,2),(2,2),(3,2)],
        [(1,0),(1,1),(1,2),(1,3)],
        [(0,1),(1,1),(2,1),(3,1)],
    ],
    "O": [
        [(0,0),(0,1),(1,0),(1,1)],
        [(0,0),(0,1),(1,0),(1,1)],
        [(0,0),(0,1),(1,0),(1,1)],
        [(0,0),(0,1),(1,0),(1,1)],
    ],
    "T": [
        [(0,1),(1,0),(1,1),(1,2)],
        [(0,1),(1,1),(1,2),(2,1)],
        [(1,0),(1,1),(1,2),(2,1)],
        [(0,1),(1,0),(1,1),(2,1)],
    ],
    "S": [
        [(0,1),(0,2),(1,0),(1,1)],
        [(0,1),(1,1),(1,2),(2,2)],
        [(1,1),(1,2),(2,0),(2,1)],
        [(0,0),(1,0),(1,1),(2,1)],
    ],
    "Z": [
        [(0,0),(0,1),(1,1),(1,2)],
        [(0,2),(1,1),(1,2),(2,1)],
        [(1,0),(1,1),(2,1),(2,2)],
        [(0,1),(1,0),(1,1),(2,0)],
    ],
    "J": [
        [(0,0),(1,0),(1,1),(1,2)],
        [(0,1),(0,2),(1,1),(2,1)],
        [(1,0),(1,1),(1,2),(2,2)],
        [(0,1),(1,1),(2,0),(2,1)],
    ],
    "L": [
        [(0,2),(1,0),(1,1),(1,2)],
        [(0,1),(1,1),(2,1),(2,2)],
        [(1,0),(1,1),(1,2),(2,0)],
        [(0,0),(0,1),(1,1),(2,1)],
    ],
}

# SRS wall-kick offsets for JLSTZ pieces
# Format: {(from_state, to_state): [(dx, dy), ...]}
_WALL_KICKS_JLSTZ: dict[tuple[int,int], list[tuple[int,int]]] = {
    (0,1): [( 0, 0),(-1, 0),(-1, 1),( 0,-2),(-1,-2)],
    (1,0): [( 0, 0),( 1, 0),( 1,-1),( 0, 2),( 1, 2)],
    (1,2): [( 0, 0),( 1, 0),( 1,-1),( 0, 2),( 1, 2)],
    (2,1): [( 0, 0),(-1, 0),(-1, 1),( 0,-2),(-1,-2)],
    (2,3): [( 0, 0),( 1, 0),( 1, 1),( 0,-2),( 1,-2)],
    (3,2): [( 0, 0),(-1, 0),(-1,-1),( 0, 2),(-1, 2)],
    (3,0): [( 0, 0),(-1, 0),(-1,-1),( 0, 2),(-1, 2)],
    (0,3): [( 0, 0),( 1, 0),( 1, 1),( 0,-2),( 1,-2)],
}

# SRS wall-kick offsets for I piece (different grid)
_WALL_KICKS_I: dict[tuple[int,int], list[tuple[int,int]]] = {
    (0,1): [( 0, 0),(-2, 0),( 1, 0),(-2,-1),( 1, 2)],
    (1,0): [( 0, 0),( 2, 0),(-1, 0),( 2, 1),(-1,-2)],
    (1,2): [( 0, 0),(-1, 0),( 2, 0),(-1, 2),( 2,-1)],
    (2,1): [( 0, 0),( 1, 0),(-2, 0),( 1,-2),(-2, 1)],
    (2,3): [( 0, 0),( 2, 0),(-1, 0),( 2, 1),(-1,-2)],
    (3,2): [( 0, 0),(-2, 0),( 1, 0),(-2,-1),( 1, 2)],
    (3,0): [( 0, 0),( 1, 0),(-2, 0),( 1,-2),(-2, 1)],
    (0,3): [( 0, 0),(-1, 0),( 2, 0),(-1, 2),( 2,-1)],
}

_COLOR_IDS: dict[str, int] = {
    "I": 1, "O": 2, "T": 3, "S": 4, "Z": 5, "J": 6, "L": 7,
}


@dataclass
class Piece:
    # """
    # A single active tetromino.

    # Attributes:
    #     piece_type: One of "I","O","T","S","Z","J","L"
    #     rotation:   Current rotation state (0-3)
    #     x:          Column of piece's bounding-box top-left on the board
    #     y:          Row of piece's bounding-box top-left on the board
    # """

    piece_type: str
    rotation: int = 0
    x: int = 3          # default spawn column (centre-ish)
    y: int = 0          # default spawn row (top)

    # Class-level lookup (shared, not per-instance)
    _shapes: ClassVar[dict[str, list[list[tuple[int,int]]]]] = _SHAPES
    _color_ids: ClassVar[dict[str, int]] = _COLOR_IDS

    @property
    def color_id(self) -> int:
        return self._color_ids[self.piece_type]

    def get_cells(self) -> list[tuple[int, int]]:
        # """
        # Return list of (row, col) offsets for the current rotation state.
        # Add (self.y, self.x) to get absolute board coordinates.
        # """
        return self._shapes[self.piece_type][self.rotation]

    def get_wall_kicks(self, from_state: int, to_state: int) -> list[tuple[int,int]]:
        # """Return SRS wall-kick offsets for this piece type and rotation transition."""
        table = _WALL_KICKS_I if self.piece_type == "I" else _WALL_KICKS_JLSTZ
        return table.get((from_state, to_state), [(0, 0)])

    # ------------------------------------------------------------------
    # Movement helpers (return NEW piece, do NOT mutate)
    # ------------------------------------------------------------------

    def moved(self, dx: int, dy: int) -> "Piece":
        # """Return a copy of this piece shifted by (dx cols, dy rows)."""
        p = copy.copy(self)
        p.x += dx
        p.y += dy
        return p

    def rotated(self, clockwise: bool = True) -> "Piece":
        # """Return a copy rotated CW (clockwise=True) or CCW."""
        p = copy.copy(self)
        delta = 1 if clockwise else -1
        p.rotation = (self.rotation + delta) % 4
        return p

    def ghost(self, board) -> "Piece":
        # """
        # Return a copy of this piece dropped to the lowest valid row.
        # Used by renderer to draw the ghost/shadow piece.
        # """
        g = copy.copy(self)
        while board.is_valid_position(g, g.x, g.y + 1):
            g.y += 1
        return g

    def __repr__(self) -> str:
        return f"Piece({self.piece_type}, rot={self.rotation}, x={self.x}, y={self.y})"


# ---------------------------------------------------------------------------
# Piece bag (7-bag randomiser — standard Tetris guideline)
# ---------------------------------------------------------------------------

import random

class PieceBag:
    # """
    # Generates pieces using the 7-bag system:
    # each bag contains exactly one of each piece type in random order.
    # Prevents long droughts of any single piece.
    # """

    PIECE_TYPES: ClassVar[list[str]] = list(_SHAPES.keys())

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._bag: list[str] = []

    def _refill(self) -> None:
        self._bag = self.PIECE_TYPES[:]
        self._rng.shuffle(self._bag)

    def next(self) -> Piece:
        # """Pop the next piece from the bag, refilling when empty."""
        if not self._bag:
            self._refill()
        piece_type = self._bag.pop()
        # Spawn at column 3 (centres a 4-wide piece in 10-col grid)
        return Piece(piece_type=piece_type, rotation=0, x=3, y=0)

    def peek(self) -> str:
        # """Look at the next piece type without consuming it (for preview)."""
        if not self._bag:
            self._refill()
        return self._bag[-1]