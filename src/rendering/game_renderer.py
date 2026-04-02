# """
# game_renderer.py
# ────────────────
# Pygame renderer for the Tetris board, pieces, and ghost piece.
# Responsible ONLY for drawing game-state visuals onto a Surface.
# """

from __future__ import annotations

import pygame
from typing import Optional, Tuple

# ── colour palette ──────────────────────────────────────────────────────────
COLOURS = {
    "background": (10, 10, 20),
    "grid":       (30, 30, 50),
    "border":     (80, 80, 120),
    "ghost":      (60, 60, 80),
    # tetrominoes  (I   O      T       S       Z       J       L)
    "I": (0,   240, 240),
    "O": (240, 240,   0),
    "T": (160,   0, 240),
    "S": (0,   240,   0),
    "Z": (240,   0,   0),
    "J": (0,    0,  240),
    "L": (240, 160,   0),
    "empty":      (15, 15, 28),
}

PIECE_COLOUR_MAP = {
    1: "I", 2: "O", 3: "T", 4: "S", 5: "Z", 6: "J", 7: "L",
}


class GameRenderer:
    # """
    # Draws the Tetris play-field (board + falling piece + ghost) onto a
    # pygame.Surface.  All sizing is derived from ``cell_size`` so the
    # renderer scales gracefully.

    # Parameters
    # ----------
    # surface     : pygame.Surface  – target surface to draw onto
    # board_cols  : int             – board width  (default 10)
    # board_rows  : int             – board height (default 20)
    # cell_size   : int             – pixel size of one cell (default 30)
    # origin      : tuple[int,int]  – top-left pixel of the board area
    # """

    def __init__(
        self,
        surface: pygame.Surface,
        board_cols: int = 10,
        board_rows: int = 20,
        cell_size: int = 30,
        origin: Tuple[int, int] = (0, 0),
    ) -> None:
        self.surface    = surface
        self.cols       = board_cols
        self.rows       = board_rows
        self.cell_size  = cell_size
        self.origin     = origin
        self.cs         = cell_size          # shorthand

        self.board_px_w = self.cols * self.cs
        self.board_px_h = self.rows * self.cs

    # ── public API ───────────────────────────────────────────────────────────

    def draw_frame(
        self,
        grid: list[list[int]],
        current_piece,          # piece.Piece  (may be None)
        game_state,             # game_state.GameState
    ) -> None:
        """Render one complete frame of the board."""
        self._draw_background()
        self._draw_grid_lines()
        self._draw_board_cells(grid)

        if current_piece is not None:
            ghost_y = self._calc_ghost_y(grid, current_piece)
            self._draw_ghost(current_piece, ghost_y)
            self._draw_piece(current_piece)

        self._draw_border()

    # ── private helpers ──────────────────────────────────────────────────────

    def _draw_background(self) -> None:
        ox, oy = self.origin
        rect = pygame.Rect(ox, oy, self.board_px_w, self.board_px_h)
        pygame.draw.rect(self.surface, COLOURS["background"], rect)

    def _draw_grid_lines(self) -> None:
        ox, oy = self.origin
        colour = COLOURS["grid"]
        for c in range(self.cols + 1):
            x = ox + c * self.cs
            pygame.draw.line(self.surface, colour, (x, oy),
                             (x, oy + self.board_px_h))
        for r in range(self.rows + 1):
            y = oy + r * self.cs
            pygame.draw.line(self.surface, colour, (ox, y),
                             (ox + self.board_px_w, y))

    def _draw_board_cells(self, grid: list[list[int]]) -> None:
        for r, row in enumerate(grid):
            for c, cell in enumerate(row):
                if cell:
                    colour_key = PIECE_COLOUR_MAP.get(cell, "I")
                    self._draw_cell(r, c, COLOURS[colour_key])
                else:
                    self._draw_cell(r, c, COLOURS["empty"], outline=True)

    def _draw_piece(self, piece) -> None:
        colour_key = PIECE_COLOUR_MAP.get(piece.color_id, "I")
        colour = COLOURS[colour_key]
        for r, c in piece.get_cells():
            abs_r = r + piece.y
            abs_c = c + piece.x
            if abs_r >= 0:
                self._draw_cell(abs_r, abs_c, colour)

    def _draw_ghost(self, piece, ghost_y: int) -> None:
        colour = COLOURS["ghost"]
        dy = ghost_y - piece.y
        for r, c in piece.get_cells():
            abs_r = r + piece.y + dy
            abs_c = c + piece.x
            if abs_r >= 0:
                self._draw_cell(abs_r, abs_c, colour, outline=True)

    def _draw_border(self) -> None:
        ox, oy = self.origin
        rect = pygame.Rect(ox, oy, self.board_px_w, self.board_px_h)
        pygame.draw.rect(self.surface, COLOURS["border"], rect, 2)

    def _draw_cell(
        self,
        row: int,
        col: int,
        colour: Tuple[int, int, int],
        outline: bool = False,
    ) -> None:
        ox, oy = self.origin
        pad = 1
        x = ox + col * self.cs + pad
        y = oy + row * self.cs + pad
        w = h = self.cs - pad * 2
        rect = pygame.Rect(x, y, w, h)

        if outline:
            pygame.draw.rect(self.surface, colour, rect, 1)
        else:
            pygame.draw.rect(self.surface, colour, rect)
            # highlight edge for 3-D feel
            light = tuple(min(c + 60, 255) for c in colour)
            dark  = tuple(max(c - 60, 0)   for c in colour)
            pygame.draw.line(self.surface, light, rect.topleft,     rect.topright)
            pygame.draw.line(self.surface, light, rect.topleft,     rect.bottomleft)
            pygame.draw.line(self.surface, dark,  rect.bottomleft,  rect.bottomright)
            pygame.draw.line(self.surface, dark,  rect.topright,    rect.bottomright)

    # ── ghost calculation ────────────────────────────────────────────────────

    def _calc_ghost_y(self, grid: list[list[int]], piece) -> int:
        """Drop the piece as far as possible and return the landing row."""
        test_y = piece.y
        while not self._collides(grid, piece, test_y + 1):
            test_y += 1
        return test_y

    def _collides(self, grid: list[list[int]], piece, test_y: int) -> bool:
        dy = test_y - piece.y
        for r, c in piece.get_cells():
            nr = r + dy
            if nr >= self.rows:
                return True
            if 0 <= nr < self.rows and 0 <= c < self.cols:
                if grid[nr][c]:
                    return True
        return False