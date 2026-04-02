"""
game_state.py — Tetris game state machine

Manages:
- Active piece + next-piece preview
- Gravity tick and soft/hard drop
- Score using Nintendo BPS formula
- Level progression and speed scaling
- Game-over flag
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto

from game.board import Board
from game.piece import Piece, PieceBag


# ---------------------------------------------------------------------------
# Score table (Nintendo BPS — points × level)
# ---------------------------------------------------------------------------
_LINE_SCORE: dict[int, int] = {
    0: 0,
    1: 100,
    2: 300,
    3: 500,
    4: 800,   # Tetris!
}

# Frames-per-cell gravity at each level (60 fps base)
# Source: Tetris guideline gravity table
_GRAVITY_FRAMES: dict[int, int] = {
    1: 48, 2: 43, 3: 38, 4: 33, 5: 28,
    6: 23, 7: 18, 8: 13, 9:  8, 10: 6,
    11: 5, 12: 5, 13: 4, 14: 4, 15: 3,
    16: 3, 17: 2, 18: 2, 19: 1, 20: 1,
}
_MAX_LEVEL = max(_GRAVITY_FRAMES.keys())

# Lines required to advance to next level
_LINES_PER_LEVEL = 10


class GamePhase(Enum):
    PLAYING  = auto()
    PAUSED   = auto()
    GAME_OVER = auto()


@dataclass
class GameState:
    """
    Central game state — owns board, current piece, score, and level.

    Typical usage:
        gs = GameState()
        gs.start()

        # each frame:
        gs.tick()                   # gravity
        gs.move_left() / move_right() / rotate() / soft_drop() / hard_drop()

        # render:
        gs.board.grid               # board cells
        gs.current_piece            # active piece
        gs.ghost_piece              # shadow piece
        gs.next_piece_type          # preview
    """

    seed: int | None = None

    # --- runtime state (initialised in start()) ---
    board: Board = field(default_factory=Board)
    bag: PieceBag = field(init=False)

    current_piece: Piece | None = field(default=None, init=False)
    next_piece_type: str = field(default="", init=False)

    score: int = field(default=0, init=False)
    level: int = field(default=1, init=False)
    lines_cleared: int = field(default=0, init=False)

    phase: GamePhase = field(default=GamePhase.GAME_OVER, init=False)

    _gravity_counter: int = field(default=0, init=False, repr=False)
    _lock_delay: int = field(default=0, init=False, repr=False)   # frames on ground
    _LOCK_DELAY_FRAMES: int = field(default=30, init=False, repr=False)

    def __post_init__(self) -> None:
        self.bag = PieceBag(seed=self.seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Reset everything and begin a new game."""
        self.board.reset()
        self.bag = PieceBag(seed=self.seed)
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self._gravity_counter = 0
        self._lock_delay = 0
        self.phase = GamePhase.PLAYING
        self._spawn_next()

    def tick(self) -> None:
        """
        Advance one game frame (call once per frame at 60 fps).
        Handles gravity, lock delay, line clear, and spawn.
        """
        if self.phase != GamePhase.PLAYING or self.current_piece is None:
            return

        self._gravity_counter += 1
        gravity_threshold = _GRAVITY_FRAMES.get(self.level, 1)

        if self._gravity_counter >= gravity_threshold:
            self._gravity_counter = 0
            self._apply_gravity()

    def move_left(self) -> bool:
        return self._try_move(-1, 0)

    def move_right(self) -> bool:
        return self._try_move(1, 0)

    def soft_drop(self) -> bool:
        """Move piece down one row; awards 1 point if successful."""
        moved = self._try_move(0, 1)
        if moved:
            self.score += 1
        return moved

    def hard_drop(self) -> None:
        """Instantly drop piece to lowest valid row; awards 2 pts per row."""
        if self.current_piece is None:
            return
        rows_dropped = 0
        while self._try_move(0, 1):
            rows_dropped += 1
        self.score += rows_dropped * 2
        self._lock_piece()

    def rotate(self, clockwise: bool = True) -> bool:
        """
        Attempt SRS rotation with wall-kick fallback.
        Returns True if rotation succeeded.
        """
        if self.current_piece is None:
            return False

        from_state = self.current_piece.rotation
        candidate = self.current_piece.rotated(clockwise)
        to_state = candidate.rotation
        kicks = self.current_piece.get_wall_kicks(from_state, to_state)

        for dx, dy in kicks:
            test_x = candidate.x + dx
            test_y = candidate.y + dy
            if self.board.is_valid_position(candidate, test_x, test_y):
                candidate.x = test_x
                candidate.y = test_y
                self.current_piece = candidate
                self._lock_delay = 0    # reset lock delay on successful rotate
                return True

        return False

    def toggle_pause(self) -> None:
        if self.phase == GamePhase.PLAYING:
            self.phase = GamePhase.PAUSED
        elif self.phase == GamePhase.PAUSED:
            self.phase = GamePhase.PLAYING

    # ------------------------------------------------------------------
    # Ghost piece (for renderer)
    # ------------------------------------------------------------------

    @property
    def ghost_piece(self) -> Piece | None:
        if self.current_piece is None:
            return None
        return self.current_piece.ghost(self.board)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _try_move(self, dx: int, dy: int) -> bool:
        if self.current_piece is None:
            return False
        candidate = self.current_piece.moved(dx, dy)
        if self.board.is_valid_position(candidate, candidate.x, candidate.y):
            self.current_piece = candidate
            if dy == 0:                 # horizontal move resets lock delay
                self._lock_delay = 0
            return True
        return False

    def _apply_gravity(self) -> None:
        """Drop piece one row; if blocked, handle lock delay."""
        if self.current_piece is None:
            return

        can_drop = self.board.is_valid_position(
            self.current_piece,
            self.current_piece.x,
            self.current_piece.y + 1,
        )

        if can_drop:
            self.current_piece.y += 1
            self._lock_delay = 0
        else:
            self._lock_delay += 1
            if self._lock_delay >= self._LOCK_DELAY_FRAMES:
                self._lock_piece()

    def _lock_piece(self) -> None:
        """Freeze active piece, clear lines, update score, spawn next."""
        if self.current_piece is None:
            return

        self.board.lock_piece(
            self.current_piece,
            self.current_piece.x,
            self.current_piece.y,
        )
        self._lock_delay = 0
        self._gravity_counter = 0

        if self.board.is_game_over():
            self.phase = GamePhase.GAME_OVER
            return

        cleared = self.board.clear_lines()
        self._update_score(cleared)
        self._spawn_next()

    def _update_score(self, lines: int) -> None:
        self.score += _LINE_SCORE.get(lines, 0) * self.level
        self.lines_cleared += lines
        new_level = self.lines_cleared // _LINES_PER_LEVEL + 1
        self.level = min(new_level, _MAX_LEVEL)

    def _spawn_next(self) -> None:
        self.current_piece = self.bag.next()
        self.next_piece_type = self.bag.peek()

        # Immediate collision after spawn = top-out (game over)
        if not self.board.is_valid_position(
            self.current_piece,
            self.current_piece.x,
            self.current_piece.y,
        ):
            self.phase = GamePhase.GAME_OVER