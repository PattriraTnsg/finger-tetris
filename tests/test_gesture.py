import cv2
import mediapipe as mp
from gesture_classifier import GestureClassifier
from finger_tracker import FingerTracker

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)

classifier = GestureClassifier()
tracker = FingerTracker(smoothing=5)

cap = cv2.VideoCapture(0)
print("ทดสอบ gesture — กด Q ออก")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    action = "IDLE"

    if result.multi_hand_landmarks:
        lm = result.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)

        gesture = classifier.classify(lm.landmark)

        if gesture == "POINT":
            move = tracker.update(lm.landmark[8].x)
            action = move if move != "NONE" else "POINT (center)"
        else:
            action = gesture

    # แสดงผล
    color = {
        "MOVE_LEFT":  (255, 100, 0),
        "MOVE_RIGHT": (0, 100, 255),
        "ROTATE":     (0, 255, 100),
        "HARD_DROP":  (0, 0, 255),
    }.get(action, (200, 200, 200))

    cv2.putText(frame, f"ACTION: {action}", (10, 45),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

    cv2.imshow("Gesture Test", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()