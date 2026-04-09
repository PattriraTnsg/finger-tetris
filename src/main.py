"""
main.py  –  Finger Control Tetris  |  entry point
──────────────────────────────────────────────────
Game loop integrating:
  Detection layer  →  hand_detector + gesture_classifier + finger_tracker
  Game engine      →  board, piece, game_state, input_handler
  Rendering layer  →  game_renderer (Pygame) + camera_overlay (OpenCV) + hud
"""

from __future__ import annotations

import sys
import os

# ── make sure src/ subfolders resolve correctly ───────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
import mediapipe as mp
import pygame

from detection.gesture_classifier import GestureClassifier
from detection.finger_tracker     import FingerTracker

from game.game_state    import GameState, GamePhase
from game.input_handler import InputHandler, GestureAction

from rendering.game_renderer  import GameRenderer
from rendering.camera_overlay import CameraOverlay
from rendering.hud            import HUD

# ── window layout ─────────────────────────────────────────────────────────────
CELL_SIZE  = 40
BOARD_COLS = 10
BOARD_ROWS = 20
HUD_WIDTH  = 250
CAM_HEIGHT = 180
CAM_WIDTH  = int(CAM_HEIGHT * 4 / 3)   # 240

BOARD_PX_W = BOARD_COLS * CELL_SIZE    # 300
BOARD_PX_H = BOARD_ROWS * CELL_SIZE    # 600

WIN_W = BOARD_PX_W + HUD_WIDTH         # 480
WIN_H = BOARD_PX_H                     # 600

TARGET_FPS = 60

# ── gesture string → GestureAction map ───────────────────────────────────────
_GESTURE_MAP: dict[str, GestureAction] = {
    "MOVE_LEFT":  GestureAction.LEFT,
    "MOVE_RIGHT": GestureAction.RIGHT,
    "ROTATE":     GestureAction.ROTATE,
    "HARD_DROP":  GestureAction.DROP,
    "IDLE":       GestureAction.NONE,
}


def _resolve_gesture(gesture_label: str, tracker: FingerTracker) -> GestureAction:
    """
    Convert classifier output + finger position → GestureAction.
    POINT gesture delegates to FingerTracker for LEFT/RIGHT.
    """
    if gesture_label == "POINT":
        move = tracker.update(tracker.smooth_x)
        return _GESTURE_MAP.get(move, GestureAction.NONE)
    return _GESTURE_MAP.get(gesture_label, GestureAction.NONE)


def main() -> None:
    # ── pygame init ──────────────────────────────────────────────────────────
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H), pygame.RESIZABLE | pygame.SCALED)
    pygame.display.set_caption("Finger Control Tetris")
    clock  = pygame.time.Clock()

    board_surface = pygame.Surface((BOARD_PX_W, BOARD_PX_H))
    hud_surface   = pygame.Surface((HUD_WIDTH, WIN_H))

    # ── mediapipe hands ──────────────────────────────────────────────────────
    mp_hands = mp.solutions.hands
    hands    = mp_hands.Hands(max_num_hands=1,
                               min_detection_confidence=0.7,
                               min_tracking_confidence=0.6)

    # ── detection layer ──────────────────────────────────────────────────────
    classifier = GestureClassifier()
    tracker    = FingerTracker(smoothing=5)

    # ── game engine ──────────────────────────────────────────────────────────
    gs      = GameState()
    handler = InputHandler(gs)
    gs.start()

    # ── rendering layer ──────────────────────────────────────────────────────
    renderer    = GameRenderer(board_surface, BOARD_COLS, BOARD_ROWS, CELL_SIZE)
    cam_overlay = CameraOverlay(flip_horizontal=True)
    hud         = HUD(hud_surface, HUD_WIDTH, WIN_H)

    # ── webcam ───────────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[WARNING] No webcam found – running without gesture control.")
        

    # ── fps tracking ─────────────────────────────────────────────────────────
    fps_samples = [float(TARGET_FPS)] * 10
    fps_idx     = 0

    # peek at next piece for HUD (create a temporary bag view)
    def _next_piece_for_hud():
        """Return a Piece of the upcoming type for HUD preview."""
        from game.piece import Piece
        if gs.next_piece_type:
            return Piece(piece_type=gs.next_piece_type)
        return None

    running = True
    while running:
        clock.tick(TARGET_FPS)

        # rolling fps average
        fps_samples[fps_idx] = clock.get_fps()
        fps_idx = (fps_idx + 1) % len(fps_samples)
        smooth_fps = sum(fps_samples) / len(fps_samples)

        # ── webcam + detection ───────────────────────────────────────────────
        gesture_label = ""
        landmarks     = None
        cam_frame     = None
        tracked_xy    = None

        if cap.isOpened():
            ret, raw_frame = cap.read()
            if ret:
                rgb    = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2RGB)
                result = hands.process(rgb)

                if result.multi_hand_landmarks:
                    lm_list   = result.multi_hand_landmarks[0]
                    landmarks = lm_list.landmark

                    gesture_label = classifier.classify(landmarks)

                    # update tracker with index-tip x position (landmark 8)
                    index_x = landmarks[8].x
                    tracker.update(index_x)

                    tracked_xy = (tracker.smooth_x, landmarks[8].y)

                cam_frame = cam_overlay.draw(
                    raw_frame, landmarks, gesture_label,
                    tracked_xy, fps=smooth_fps,
                )

        # ── pygame events ────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
                if event.key == pygame.K_p:
                    gs.toggle_pause()
                if event.key == pygame.K_r:
                    gs.start()   # R restarts anytime (not just game over)
                # keyboard fallback controls
                if event.key == pygame.K_LEFT:
                    gs.move_left()
                if event.key == pygame.K_RIGHT:
                    gs.move_right()
                if event.key == pygame.K_UP:
                    gs.rotate(clockwise=True)
                if event.key == pygame.K_DOWN:
                    gs.soft_drop()
                if event.key == pygame.K_SPACE:
                    gs.hard_drop()

        # ── gesture → game action ────────────────────────────────────────────
        action = _resolve_gesture(gesture_label, tracker)
        
        # ดักจับ PAUSE แยกออกมาถ้าใน GestureAction ไม่มี enum ของ PAUSE
        if gesture_label == "PAUSE":
            gs.toggle_pause()
        else:
            handler.handle(action)

        # ── game tick (gravity) ──────────────────────────────────────────────
        gs.tick()

        # ── render board ─────────────────────────────────────────────────────
        renderer.draw_frame(gs.board.grid, gs.current_piece, gs)
        screen.blit(board_surface, (0, 0))

        # ── render HUD ───────────────────────────────────────────────────────
        debug = None
        if gesture_label or tracked_xy:
            debug = {
                "gesture": gesture_label or "—",
                "x": f"{tracked_xy[0]:.2f}" if tracked_xy else "—",
            }

        hud.draw(
            score      = gs.score,
            level      = gs.level,
            lines      = gs.lines_cleared,
            fps        = smooth_fps,
            next_piece = _next_piece_for_hud(),
            game_over  = gs.phase == GamePhase.GAME_OVER,
            paused     = gs.phase == GamePhase.PAUSED,
            debug_info = debug,
        )
        screen.blit(hud_surface, (BOARD_PX_W, 0))

        # ── camera thumbnail (bottom-right of HUD column) ────────────────────
        if cam_frame is not None:
            thumb   = cv2.resize(cam_frame, (CAM_WIDTH, CAM_HEIGHT))
            thumb   = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
            pg_surf = pygame.surfarray.make_surface(thumb.swapaxes(0, 1))
            tx = WIN_W - CAM_WIDTH - 4
            ty = WIN_H - CAM_HEIGHT - 4
            screen.blit(pg_surf, (tx, ty))

        pygame.display.flip()

    # ── cleanup ──────────────────────────────────────────────────────────────
    hands.close()
    if cap.isOpened():
        cap.release()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()