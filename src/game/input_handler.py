# """
# input_handler.py — Gesture → Game Action bridge

# Sits between the AI detection layer and game engine.
# Responsibilities:
# - Map GestureAction enum → GameState method calls
# - Debounce / cooldown so one gesture = one action (no key repeat spam)
# - Per-action cooldown tuning (rotate needs longer cooldown than move)
# """

from __future__ import annotations
import time
from enum import Enum, auto

from game.game_state import GameState, GamePhase


class GestureAction(Enum):
    # """Mirrors output from gesture_classifier.py."""
    NONE    = auto()
    LEFT    = auto()
    RIGHT   = auto()
    ROTATE  = auto()
    DROP    = auto()
    PAUSE   = auto()


# Cooldown in seconds per action type.
# Tune these after playtesting — these are sensible starting defaults.
_COOLDOWNS: dict[GestureAction, float] = {
    GestureAction.NONE:   0.0,
    GestureAction.LEFT:   0.10,   # ~6-7 moves/sec max
    GestureAction.RIGHT:  0.10,
    GestureAction.ROTATE: 0.50,   # rotation needs more deliberate gesture
    GestureAction.DROP:   0.60,   # hard drop is destructive — long guard
    GestureAction.PAUSE:  0.50,
}


class InputHandler:
    # """
    # Translates a stream of GestureAction values into GameState mutations.

    # Usage:
    #     handler = InputHandler(game_state)
    #     # each frame:
    #     gesture = classifier.classify(frame)
    #     handler.handle(gesture)
    # """

    def __init__(self, game_state: GameState) -> None:
        self.gs = game_state
        # Track last fired time per action for cooldown
        self._last_fired: dict[GestureAction, float] = {
            action: 0.0 for action in GestureAction
        }

    def handle(self, action: GestureAction) -> bool:
        # """
        # Process a gesture action.

        # Returns True if the action was executed (not blocked by cooldown).
        # """
        if action == GestureAction.NONE:
            return False

        if not self._cooldown_ready(action):
            return False

        executed = self._dispatch(action)
        if executed:
            self._last_fired[action] = time.monotonic()
        return executed

    def reset_cooldowns(self) -> None:
        # """Clear all cooldown timers (e.g. after pause/resume)."""
        for key in self._last_fired:
            self._last_fired[key] = 0.0

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _cooldown_ready(self, action: GestureAction) -> bool:
        elapsed = time.monotonic() - self._last_fired[action]
        return elapsed >= _COOLDOWNS[action]

    def _dispatch(self, action: GestureAction) -> bool:
        # """Route action to the appropriate GameState method."""
        gs = self.gs

        if action == GestureAction.PAUSE:
            gs.toggle_pause()
            return True

        # Ignore game actions when not actively playing
        if gs.phase != GamePhase.PLAYING:
            return False

        if action == GestureAction.LEFT:
            return gs.move_left()

        if action == GestureAction.RIGHT:
            return gs.move_right()

        if action == GestureAction.ROTATE:
            return gs.rotate(clockwise=True)

        if action == GestureAction.DROP:
            gs.hard_drop()
            return True

        return False