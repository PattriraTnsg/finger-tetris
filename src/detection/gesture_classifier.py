import time
from collections import deque

class GestureClassifier:
    """
    Rule-based gesture classifier
    ใช้ MediaPipe landmark 21 จุด → ตรวจว่านิ้วไหน 'ตั้ง' อยู่
    """

    # landmark index ของปลายนิ้วและข้อกลาง
    FINGER_TIPS = [8, 12, 16, 20]   # ชี้, กลาง, นาง, ก้อย
    FINGER_PIPS = [6, 10, 14, 18]   # ข้อกลางของแต่ละนิ้ว

    def __init__(self):
        self.wrist_y_history = deque(maxlen=5)
        self.prev_pose = "IDLE"
        self.peace_start_time = 0
        self.fist_start_time = 0
        
    def get_fingers_up(self, landmarks) -> list[bool]:
        fingers = []
        for tip, pip in zip(self.FINGER_TIPS, self.FINGER_PIPS):
            fingers.append(landmarks[tip].y < landmarks[pip].y)
        return fingers

    def classify(self, landmarks) -> str:
        if landmarks is None:
            self.wrist_y_history.clear()
            self.peace_start_time = 0
            self.fist_start_time = 0  # รีเซ็ตเวลากำหมัดด้วย
            return "IDLE"

        fingers = self.get_fingers_up(landmarks)
        index, middle, ring, pinky = fingers
        
        is_fist = not any(fingers)
        is_open = all(fingers)

        # ── 1. เช็ค Hard Drop (กำหมัดค้าง 3 วินาที) ─────────────────────
        if is_fist:
            if self.fist_start_time == 0:
                self.fist_start_time = time.time()
            elif time.time() - self.fist_start_time > 2.5:
                self.fist_start_time = 0  # รีเซ็ตเวลาหลังจากทำสำเร็จ
                
                # ทริกเกอร์สำคัญ: เปลี่ยน prev_pose เป็น "OTHER" 
                # เพื่อป้องกันไม่ให้เกมจับว่าเป็นการ Rotate ตอนที่คุณแบมือออกหลังทำ Hard Drop
                self.prev_pose = "OTHER" 
                return "HARD_DROP"
        else:
            self.fist_start_time = 0  # ยกเลิกจับเวลาถ้าเลิกกำหมัดกลางคัน

        # ── 2. เช็ค Rotate (กำหมัดแล้วเปิดมือ) ─────────────────────
        if is_open and self.prev_pose == "FIST":
            self.prev_pose = "OPEN"
            return "ROTATE"
        
        # อัปเดตสถานะมือ
        if is_fist:
            self.prev_pose = "FIST"
        elif is_open:
            self.prev_pose = "OPEN"
        else:
            self.prev_pose = "OTHER"

        # ── 3. เช็ค Pause (Peace Sign ✌️ ค้าง 1 วินาที) ──────────────
        # หมายเหตุ: ระหว่างทำ peace sign ระบบจะ return IDLE (ไม่ขยับ)
        # เพื่อป้องกัน accidental move ขณะกำลังพยายาม pause
        if index and middle and not ring and not pinky:
            if self.peace_start_time == 0:
                self.peace_start_time = time.time()
            elif time.time() - self.peace_start_time > 1.0:
                self.peace_start_time = 0
                return "PAUSE"
            return "IDLE"
        else:
            self.peace_start_time = 0

        # ── 4. เช็ค Move Left/Right ────────────────────────────────
        if index or is_open:
            return "POINT"

        return "IDLE"