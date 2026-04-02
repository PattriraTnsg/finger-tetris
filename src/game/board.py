# """
# board.py — Tetris 10×20 grid state management

# Responsibilities:
# - Store grid state (0 = empty, 1-7 = piece color id)
# - Collision detection
# - Locking pieces into grid
# - Line clear logic
# - Game-over detection
# """

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.piece import Piece

COLS = 10
ROWS = 20
SPAWN_ROWS = 2  # invisible rows above visible grid used for game-over check


class Board:
    """Represents the 10×20 Tetris playfield."""

    def __init__(self) -> None:
        self.grid: list[list[int]] = self._empty_grid()
        self.lines_cleared_total: int = 0

    # ------------------------------------------------------------------
    # Grid helpers
    # ------------------------------------------------------------------

    def _empty_grid(self) -> list[list[int]]:
        """Return a blank 20-row × 10-col grid filled with 0."""
        return [[0] * COLS for _ in range(ROWS)]

    def reset(self) -> None:
        """Clear the board for a new game."""
        self.grid = self._empty_grid()
        self.lines_cleared_total = 0

    def get_cell(self, row: int, col: int) -> int:
        """Return color id at (row, col), or -1 if out of bounds."""
        if 0 <= row < ROWS and 0 <= col < COLS:
            return self.grid[row][col]
        return -1

    # ------------------------------------------------------------------
    # Collision detection
    # ------------------------------------------------------------------

    def is_valid_position(self, piece: "Piece", offset_x: int, offset_y: int) -> bool:
        # """
        # Check whether `piece` placed at board position (offset_x, offset_y)
        # is free of wall/floor/other-piece collisions.

        # Args:
        #     piece: the active Piece (uses piece.get_cells())
        #     offset_x: column of piece's top-left corner
        #     offset_y: row of piece's top-left corner

        # Returns:
        #     True if the position is legal.
        # """
        for row, col in piece.get_cells():
            board_row = row + offset_y
            board_col = col + offset_x

            # Out of bounds (left / right / floor)
            if board_col < 0 or board_col >= COLS:
                return False
            if board_row >= ROWS:
                return False

            # Allow piece to be partially above the visible grid (spawn zone)
            if board_row < 0:
                continue

            # Overlap with locked piece
            if self.grid[board_row][board_col] != 0:
                return False

        return True

    # ------------------------------------------------------------------
    # Locking & line clearing
    # ------------------------------------------------------------------

    def lock_piece(self, piece: "Piece", offset_x: int, offset_y: int) -> None:
        # """
        # Freeze the piece into the grid at (offset_x, offset_y).
        # Call this when the piece can no longer move down.
        # """
        for row, col in piece.get_cells():
            board_row = row + offset_y
            board_col = col + offset_x
            if 0 <= board_row < ROWS and 0 <= board_col < COLS:
                self.grid[board_row][board_col] = piece.color_id

    def clear_lines(self) -> int:
        # """
        # Remove all full rows, shift rows above down.

        # Returns:
        #     Number of lines cleared (0-4).
        # """
        full_rows = [r for r in range(ROWS) if all(self.grid[r])]

        if not full_rows:
            return 0

        # Remove full rows
        new_grid = [row for r, row in enumerate(self.grid) if r not in full_rows]
        # Prepend empty rows at the top
        empty_rows = [[0] * COLS for _ in range(len(full_rows))]
        self.grid = empty_rows + new_grid

        self.lines_cleared_total += len(full_rows)
        return len(full_rows)

    # ------------------------------------------------------------------
    # Game-over detection
    # ------------------------------------------------------------------

    def is_game_over(self) -> bool:
        # """
        # Return True if any cell in the top SPAWN_ROWS rows is occupied.
        # Called after locking a piece to check stack-out condition.
        # """
        for row in range(SPAWN_ROWS):
            if any(self.grid[row]):
                return True
        return False

    # ------------------------------------------------------------------
    # Debug / test helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        lines = []
        for row in self.grid:
            lines.append("|" + "".join(str(c) if c else "." for c in row) + "|")
        lines.append("+" + "-" * COLS + "+")
        return "\n".join(lines)