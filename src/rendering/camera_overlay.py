# """
# camera_overlay.py
# ─────────────────
# Draws MediaPipe hand landmarks, gesture label, and finger tracking
# crosshair on top of the live webcam frame (OpenCV / NumPy image).

# All drawing happens on the BGR numpy array that OpenCV uses, so this
# module has **zero** Pygame dependency and can be tested headlessly.
# """

from __future__ import annotations

import cv2
import numpy as np
from typing import Optional, Tuple, List

# ── visual constants ──────────────────────────────────────────────────────────
LANDMARK_COLOUR   = (0, 255, 180)   # cyan-green
CONNECTION_COLOUR = (255, 200, 0)   # amber
FINGERTIP_COLOUR  = (0, 120, 255)   # orange

LABEL_BG          = (20, 20, 20)
LABEL_FG          = (0, 255, 180)

CROSSHAIR_COLOUR  = (255, 80, 80)   # red crosshair for tracked finger
CROSSHAIR_RADIUS  = 18

FONT              = cv2.FONT_HERSHEY_SIMPLEX

# MediaPipe hand connections (21 landmarks, 20 connections)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),           # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),           # index
    (0, 9), (9, 10), (10, 11), (11, 12),       # middle
    (0, 13), (13, 14), (14, 15), (15, 16),     # ring
    (0, 17), (17, 18), (18, 19), (19, 20),     # pinky
    (5, 9), (9, 13), (13, 17),                 # palm
]

# Fingertip landmark indices
FINGERTIP_IDS = [4, 8, 12, 16, 20]


class CameraOverlay:
    # """
    # Composites hand-detection visualisation onto a raw webcam frame.

    # Usage
    # -----
    # overlay = CameraOverlay(show_connections=True, show_fingertips=True)
    # frame   = overlay.draw(frame, landmarks, gesture_label, tracked_xy)
    # """

    def __init__(
        self,
        show_connections: bool = True,
        show_fingertips:  bool = True,
        show_all_landmarks: bool = True,
        flip_horizontal: bool = True,          # mirror like a selfie cam
    ) -> None:
        self.show_connections    = show_connections
        self.show_fingertips     = show_fingertips
        self.show_all_landmarks  = show_all_landmarks
        self.flip_horizontal     = flip_horizontal

    # ── public API ────────────────────────────────────────────────────────────

    def draw(
        self,
        frame: np.ndarray,
        landmarks: Optional[list],              # mediapipe NormalizedLandmarkList
        gesture_label: str = "",
        tracked_xy: Optional[Tuple[float, float]] = None,   # already mirrored (0-1)
        fps: float = 0.0,
    ) -> np.ndarray:
        """
        Return a new frame with all overlays composited.
        NOTE: tracked_xy must already be in mirrored x-space (1 - raw_x).
        """
        if self.flip_horizontal:
            frame = cv2.flip(frame, 1)

        h, w = frame.shape[:2]

        if landmarks:
            # mirror landmark coords to match the flipped frame
            pts = self._normalised_to_px_mirrored(landmarks, w, h) \
                  if self.flip_horizontal \
                  else self._normalised_to_px(landmarks, w, h)

            if self.show_connections:
                self._draw_connections(frame, pts)

            if self.show_all_landmarks:
                self._draw_landmarks(frame, pts)

            if self.show_fingertips:
                self._draw_fingertips(frame, pts)

        if tracked_xy is not None:
            self._draw_crosshair(frame, tracked_xy, w, h)

        self._draw_gesture_label(frame, gesture_label)
        self._draw_fps(frame, fps)

        return frame

    # ── private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _normalised_to_px(
        landmarks: list, w: int, h: int
    ) -> List[Tuple[int, int]]:
        return [
            (int(lm.x * w), int(lm.y * h))
            for lm in landmarks
        ]

    @staticmethod
    def _normalised_to_px_mirrored(
        landmarks: list, w: int, h: int
    ) -> List[Tuple[int, int]]:
        """Mirror x so landmarks align with the flipped frame."""
        return [
            (int((1.0 - lm.x) * w), int(lm.y * h))
            for lm in landmarks
        ]

    def _draw_connections(
        self, frame: np.ndarray, pts: List[Tuple[int, int]]
    ) -> None:
        for a, b in HAND_CONNECTIONS:
            cv2.line(frame, pts[a], pts[b], CONNECTION_COLOUR, 2, cv2.LINE_AA)

    def _draw_landmarks(
        self, frame: np.ndarray, pts: List[Tuple[int, int]]
    ) -> None:
        for i, pt in enumerate(pts):
            if i in FINGERTIP_IDS:
                continue                       # handled by _draw_fingertips
            cv2.circle(frame, pt, 4, LANDMARK_COLOUR, -1, cv2.LINE_AA)
            cv2.circle(frame, pt, 4, (0, 0, 0), 1,  cv2.LINE_AA)

    def _draw_fingertips(
        self, frame: np.ndarray, pts: List[Tuple[int, int]]
    ) -> None:
        for idx in FINGERTIP_IDS:
            pt = pts[idx]
            cv2.circle(frame, pt, 7, FINGERTIP_COLOUR, -1, cv2.LINE_AA)
            cv2.circle(frame, pt, 7, (255, 255, 255), 1, cv2.LINE_AA)

    def _draw_crosshair(
        self,
        frame: np.ndarray,
        xy: Tuple[float, float],
        w: int,
        h: int,
    ) -> None:
        px = int(xy[0] * w)
        py = int(xy[1] * h)
        r  = CROSSHAIR_RADIUS
        colour = CROSSHAIR_COLOUR

        # outer circle
        cv2.circle(frame, (px, py), r, colour, 2, cv2.LINE_AA)
        # crosshair lines
        cv2.line(frame, (px - r, py), (px + r, py), colour, 1, cv2.LINE_AA)
        cv2.line(frame, (px, py - r), (px, py + r), colour, 1, cv2.LINE_AA)
        # centre dot
        cv2.circle(frame, (px, py), 3, colour, -1, cv2.LINE_AA)

    @staticmethod
    def _draw_gesture_label(frame: np.ndarray, label: str) -> None:
        if not label:
            return
        scale, thickness = 1.0, 2
        (tw, th), _ = cv2.getTextSize(label, FONT, scale, thickness)
        pad = 8
        x, y = 12, 12
        cv2.rectangle(
            frame,
            (x - pad, y - pad),
            (x + tw + pad, y + th + pad),
            LABEL_BG,
            -1,
        )
        cv2.putText(
            frame, label,
            (x, y + th),
            FONT, scale, LABEL_FG, thickness, cv2.LINE_AA,
        )

    @staticmethod
    def _draw_fps(frame: np.ndarray, fps: float) -> None:
        if fps <= 0:
            return
        h = frame.shape[0]
        text = f"FPS {fps:.1f}"
        scale, thickness = 0.55, 1
        (tw, th), _ = cv2.getTextSize(text, FONT, scale, thickness)
        cv2.putText(
            frame, text,
            (8, h - 8),
            FONT, scale, (180, 180, 180), thickness, cv2.LINE_AA,
        )