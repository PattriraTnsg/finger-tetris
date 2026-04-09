from collections import deque

class FingerTracker:
    """
    รับ x position ของมือ → smooth + เช็ค Zone
    - ซ้าย 30% (x < 0.3) = MOVE_LEFT
    - ขวา 30% (x > 0.7) = MOVE_RIGHT
    - ตรงกลาง 40% = NONE
    """

    def __init__(self, smoothing=5):
        self._history = deque(maxlen=smoothing)

    def update(self, x_normalized: float) -> str:
        # x_normalized มาจาก raw MediaPipe (ก่อน flip)
        # x=0.0 คือขวาจอ (หลัง flip), x=1.0 คือซ้ายจอ (หลัง flip)
        # ดังนั้น x < 0.30 = มือไปอยู่ขวาจอ = MOVE_RIGHT ✓
        self._history.append(x_normalized)
        smooth_x = sum(self._history) / len(self._history)

        if smooth_x < 0.30:
            return "MOVE_RIGHT"   # raw x ต่ำ = ขวาจอหลัง flip
        elif smooth_x > 0.70:
            return "MOVE_LEFT"    # raw x สูง = ซ้ายจอหลัง flip
        
        return "NONE"

    @property
    def smooth_x(self) -> float:
        if not self._history:
            return 0.5
        return sum(self._history) / len(self._history)