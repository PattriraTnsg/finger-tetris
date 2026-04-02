"""
record_demo.py
──────────────
ใช้ record หน้าจอ game เป็น .mp4 แล้วแปลงเป็น GIF สำหรับใส่ใน README

Usage:
    python record_demo.py          # record 30 วินาที
    python record_demo.py --sec 15 # record 15 วินาที

Output:
    assets/demo.mp4   ← video ต้นฉบับ
    assets/demo.gif   ← GIF สำหรับ README (resize เป็น 480p)
"""

from __future__ import annotations
import argparse
import os
import sys
import time
import subprocess

# ── ensure src/ is importable ─────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import cv2
import mediapipe as mp
import pygame
import numpy as np

from detection.gesture_classifier import GestureClassifier
from detection.finger_tracker     import FingerTracker
from game.game_state    import GameState, GamePhase
from game.input_handler import InputHandler, GestureAction
from rendering.game_renderer  import GameRenderer
from rendering.camera_overlay import CameraOverlay
from rendering.hud            import HUD

# ── layout (same as main.py) ─────────────────────────────────────────────
CELL_SIZE  = 40
BOARD_COLS = 10
BOARD_ROWS = 20
HUD_WIDTH  = 250
CAM_HEIGHT = 180
CAM_WIDTH  = int(CAM_HEIGHT * 4 / 3)

BOARD_PX_W = BOARD_COLS * CELL_SIZE
BOARD_PX_H = BOARD_ROWS * CELL_SIZE
WIN_W      = BOARD_PX_W + HUD_WIDTH
WIN_H      = BOARD_PX_H
TARGET_FPS = 60

_GESTURE_MAP = {
    "MOVE_LEFT":  GestureAction.LEFT,
    "MOVE_RIGHT": GestureAction.RIGHT,
    "ROTATE":     GestureAction.ROTATE,
    "HARD_DROP":  GestureAction.DROP,
    "IDLE":       GestureAction.NONE,
}

os.makedirs("assets", exist_ok=True)


def record(duration_sec: int = 30) -> None:
    # ── pygame init ──────────────────────────────────────────────────────
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Finger Control Tetris  [RECORDING]")
    clock  = pygame.time.Clock()

    board_surface = pygame.Surface((BOARD_PX_W, BOARD_PX_H))
    hud_surface   = pygame.Surface((HUD_WIDTH, WIN_H))

    # ── mediapipe ────────────────────────────────────────────────────────
    mp_hands = mp.solutions.hands
    hands    = mp_hands.Hands(max_num_hands=1,
                               min_detection_confidence=0.7,
                               min_tracking_confidence=0.6)

    classifier = GestureClassifier()
    tracker    = FingerTracker(smoothing=5)

    gs      = GameState()
    handler = InputHandler(gs)
    gs.start()

    renderer    = GameRenderer(board_surface, BOARD_COLS, BOARD_ROWS, CELL_SIZE)
    cam_overlay = CameraOverlay(flip_horizontal=True)
    hud         = HUD(hud_surface, HUD_WIDTH, WIN_H)

    cap = cv2.VideoCapture(0)

    # ── video writer ─────────────────────────────────────────────────────
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out    = cv2.VideoWriter("assets/demo.mp4", fourcc, 30, (WIN_W, WIN_H))

    fps_samples = [float(TARGET_FPS)] * 10
    fps_idx     = 0
    start_time  = time.time()
    frame_count = 0

    print(f"[REC] Recording {duration_sec}s → assets/demo.mp4")
    print("      Play the game normally — press Q or wait for timer to stop.")

    def _next_piece_for_hud():
        from game.piece import Piece
        if gs.next_piece_type:
            return Piece(piece_type=gs.next_piece_type)
        return None

    running = True
    while running and (time.time() - start_time) < duration_sec:
        clock.tick(TARGET_FPS)

        fps_samples[fps_idx] = clock.get_fps()
        fps_idx = (fps_idx + 1) % len(fps_samples)
        smooth_fps = sum(fps_samples) / len(fps_samples)

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
                    index_x = landmarks[8].x
                    tracker.update(index_x)
                    tracked_xy = (tracker.smooth_x, landmarks[8].y)
                cam_frame = cam_overlay.draw(
                    raw_frame, landmarks, gesture_label,
                    tracked_xy, fps=smooth_fps,
                )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                if event.key == pygame.K_p:
                    gs.toggle_pause()
                if event.key == pygame.K_r:
                    gs.start()
                if event.key == pygame.K_LEFT:   gs.move_left()
                if event.key == pygame.K_RIGHT:  gs.move_right()
                if event.key == pygame.K_UP:     gs.rotate(clockwise=True)
                if event.key == pygame.K_DOWN:   gs.soft_drop()
                if event.key == pygame.K_SPACE:  gs.hard_drop()

        if gesture_label == "PAUSE":
            gs.toggle_pause()
        else:
            action = _GESTURE_MAP.get(
                tracker.update(tracker.smooth_x) if gesture_label == "POINT" else gesture_label,
                GestureAction.NONE,
            )
            handler.handle(action)

        gs.tick()

        renderer.draw_frame(gs.board.grid, gs.current_piece, gs)
        screen.blit(board_surface, (0, 0))

        hud.draw(
            score=gs.score, level=gs.level, lines=gs.lines_cleared,
            fps=smooth_fps, next_piece=_next_piece_for_hud(),
            game_over=gs.phase == GamePhase.GAME_OVER,
            paused=gs.phase == GamePhase.PAUSED,
        )
        screen.blit(hud_surface, (BOARD_PX_W, 0))

        if cam_frame is not None:
            thumb   = cv2.resize(cam_frame, (CAM_WIDTH, CAM_HEIGHT))
            thumb   = cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB)
            pg_surf = pygame.surfarray.make_surface(thumb.swapaxes(0, 1))
            screen.blit(pg_surf, (WIN_W - CAM_WIDTH - 4, WIN_H - CAM_HEIGHT - 4))

        # ── countdown overlay ────────────────────────────────────────────
        remaining = int(duration_sec - (time.time() - start_time)) + 1
        font = pygame.font.SysFont("couriernew", 14)
        rec_text = font.render(f"● REC  {remaining}s remaining", True, (255, 80, 80))
        screen.blit(rec_text, (8, WIN_H - 20))

        pygame.display.flip()

        # ── capture frame for video ──────────────────────────────────────
        if frame_count % 2 == 0:   # capture every other frame → ~30fps
            raw_pixels = pygame.surfarray.array3d(screen)
            frame_bgr  = cv2.cvtColor(
                np.transpose(raw_pixels, (1, 0, 2)), cv2.COLOR_RGB2BGR
            )
            out.write(frame_bgr)

        frame_count += 1

    # ── cleanup ──────────────────────────────────────────────────────────
    out.release()
    hands.close()
    if cap.isOpened():
        cap.release()
    pygame.quit()

    print(f"[DONE] Saved assets/demo.mp4")
    _convert_to_gif()


def _convert_to_gif() -> None:
    """Convert demo.mp4 → demo.gif using ffmpeg (must be installed)."""
    print("[GIF]  Converting to GIF with ffmpeg...")

    cmd = [
        "ffmpeg", "-y",
        "-i", "assets/demo.mp4",
        "-vf", "fps=15,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
        "-loop", "0",
        "assets/demo.gif",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("[DONE] Saved assets/demo.gif  ← ใส่ใน README ได้เลย!")
    else:
        print("[WARN] ffmpeg ไม่ได้ติดตั้ง หรือแปลง GIF ไม่สำเร็จ")
        print("       ให้ใช้ไฟล์ assets/demo.mp4 แทน หรือแปลง GIF ด้วย:")
        print("       https://ezgif.com/video-to-gif")
        print(f"       Error: {result.stderr[-300:]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record Finger Tetris demo")
    parser.add_argument("--sec", type=int, default=30, help="Recording duration in seconds")
    args = parser.parse_args()
    record(args.sec)