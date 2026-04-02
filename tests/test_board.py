# """
# test_board.py — Unit tests for Board class

# Run:  pytest tests/test_board.py -v
# """

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'game'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from board import Board, COLS, ROWS
from piece import Piece


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def filled_piece(color_id: int = 1) -> Piece:
    """Return a 2×2 O-piece stub for deterministic tests."""
    p = Piece(piece_type="O")
    p.color_id  # just verify access
    return p


def fill_row(board: Board, row: int, except_col: int | None = None) -> None:
    """Fill a row except one column (to create almost-full rows)."""
    for col in range(COLS):
        if col != except_col:
            board.grid[row][col] = 1


# ---------------------------------------------------------------------------
# Board initialisation
# ---------------------------------------------------------------------------

class TestBoardInit:
    def test_grid_dimensions(self):
        b = Board()
        assert len(b.grid) == ROWS
        assert all(len(row) == COLS for row in b.grid)

    def test_grid_empty_on_init(self):
        b = Board()
        assert all(cell == 0 for row in b.grid for cell in row)

    def test_reset_clears_grid(self):
        b = Board()
        b.grid[5][5] = 3
        b.reset()
        assert b.grid[5][5] == 0
        assert b.lines_cleared_total == 0


# ---------------------------------------------------------------------------
# Collision detection
# ---------------------------------------------------------------------------

class TestIsValidPosition:
    def test_o_piece_valid_centre_spawn(self):
        b = Board()
        p = Piece("O")
        assert b.is_valid_position(p, 3, 0) is True

    def test_piece_out_left(self):
        b = Board()
        p = Piece("O")
        assert b.is_valid_position(p, -1, 0) is False

    def test_piece_out_right(self):
        b = Board()
        p = Piece("O")
        assert b.is_valid_position(p, COLS - 1, 0) is False  # O is 2 wide

    def test_piece_out_floor(self):
        b = Board()
        p = Piece("O")
        assert b.is_valid_position(p, 3, ROWS) is False

    def test_piece_blocked_by_locked_cell(self):
        b = Board()
        b.grid[1][4] = 2
        p = Piece("O")  # O occupies (0,0)(0,1)(1,0)(1,1) relative
        assert b.is_valid_position(p, 4, 0) is False  # would overlap row1,col4

    def test_piece_partially_above_grid_allowed(self):
        """Pieces may spawn partially above row 0 (spawn zone)."""
        b = Board()
        p = Piece("I")
        assert b.is_valid_position(p, 3, -1) is True


# ---------------------------------------------------------------------------
# Locking
# ---------------------------------------------------------------------------

class TestLockPiece:
    def test_o_piece_locked_correctly(self):
        b = Board()
        p = Piece("O")
        b.lock_piece(p, 4, 18)
        assert b.grid[18][4] == p.color_id
        assert b.grid[18][5] == p.color_id
        assert b.grid[19][4] == p.color_id
        assert b.grid[19][5] == p.color_id

    def test_lock_does_not_write_out_of_bounds(self):
        b = Board()
        p = Piece("I")
        # Place I piece horizontally at bottom — should stay within bounds
        b.lock_piece(p, 3, 19)
        assert all(0 <= b.grid[19][c] <= 7 for c in range(COLS))


# ---------------------------------------------------------------------------
# Line clearing
# ---------------------------------------------------------------------------

class TestClearLines:
    def test_no_clear_when_rows_not_full(self):
        b = Board()
        fill_row(b, 19, except_col=0)  # leave one gap
        assert b.clear_lines() == 0

    def test_single_line_clear(self):
        b = Board()
        fill_row(b, 19)
        assert b.clear_lines() == 1
        assert all(b.grid[19][c] == 0 for c in range(COLS))

    def test_tetris_clear(self):
        b = Board()
        for row in range(16, 20):
            fill_row(b, row)
        assert b.clear_lines() == 4
        assert b.lines_cleared_total == 4

    def test_rows_shift_down_after_clear(self):
        b = Board()
        b.grid[17][0] = 7   # marker above full rows
        fill_row(b, 18)
        fill_row(b, 19)
        b.clear_lines()
        # Marker should have shifted down by 2
        assert b.grid[19][0] == 7


# ---------------------------------------------------------------------------
# Game-over detection
# ---------------------------------------------------------------------------

class TestIsGameOver:
    def test_not_game_over_empty_board(self):
        assert Board().is_game_over() is False

    def test_game_over_when_top_row_occupied(self):
        b = Board()
        b.grid[0][0] = 1
        assert b.is_game_over() is True

    def test_game_over_row1_occupied(self):
        b = Board()
        b.grid[1][5] = 2
        assert b.is_game_over() is True