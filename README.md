# 🖐️ Finger Control Tetris

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-green?logo=google&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.5-red)
![OpenCV](https://img.shields.io/badge/OpenCV-4.9-blue?logo=opencv)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Play Tetris using only your hand gestures — no keyboard, no controller.**  
Real-time AI hand detection powered by MediaPipe.

<!-- Replace with your actual demo GIF after recording -->
![Demo](assets/demo.gif)

</div>

---

## ✋ Gesture Controls

| Gesture | Action |
|---|---|
| ☝️ Point finger **left zone** (x < 30%) | Move piece **Right** |
| ☝️ Point finger **right zone** (x > 70%) | Move piece **Left** |
| ✌️ Peace sign (hold 1 sec) | **Pause / Resume** |
| ✊ Fist → Open palm | **Rotate** piece |
| ✊ Fist (hold 2.5 sec) | **Hard Drop** |

> Keyboard fallback: `← →` move · `↑` rotate · `↓` soft drop · `Space` hard drop · `P` pause · `R` restart · `Q` quit

---

## 🏗️ Architecture

```
finger-tetris/
├── src/
│   ├── detection/          # AI layer
│   │   ├── hand_detector.py       # MediaPipe Hands wrapper
│   │   ├── gesture_classifier.py  # Rule-based gesture recognition
│   │   └── finger_tracker.py      # Smoothed x/y position mapping
│   ├── game/               # Game engine layer
│   │   ├── board.py               # 10×20 grid + collision detection
│   │   ├── piece.py               # Tetrominoes + SRS rotation system
│   │   ├── game_state.py          # Score, level, gravity, game loop
│   │   └── input_handler.py       # Gesture → game action bridge
│   ├── rendering/          # Rendering layer
│   │   ├── game_renderer.py       # Pygame board renderer
│   │   ├── camera_overlay.py      # Landmark overlay on webcam feed
│   │   └── hud.py                 # Score, FPS, debug panel
│   └── main.py             # Entry point / main game loop
├── tests/                  # Pytest unit tests
├── models/                 # Saved ML models (optional)
├── data/                   # Gesture dataset (optional)
└── requirements.txt
```

### Tech Stack

| Layer | Technology |
|---|---|
| Hand Detection | MediaPipe Hands (21 landmarks) |
| Gesture Classification | Rule-based classifier (extensible to ML) |
| Position Smoothing | Sliding window average (deque) |
| Game Engine | Custom Tetris with SRS rotation |
| Rendering | Pygame (board) + OpenCV (camera overlay) |
| Testing | Pytest |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Webcam
- Windows / macOS / Linux

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/finger-tetris.git
cd finger-tetris

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the game
python src/main.py
```

### Run Tests

```bash
pytest tests/ -v
```

---

## 🎮 How It Works

```
Webcam Frame
    │
    ▼
MediaPipe Hands  ──►  21 Hand Landmarks (normalized x, y, z)
    │
    ▼
GestureClassifier  ──►  Gesture Label (POINT / FIST / OPEN / PEACE)
    │
    ▼
FingerTracker  ──►  Smoothed Position → MOVE_LEFT / MOVE_RIGHT / NONE
    │
    ▼
InputHandler  ──►  Cooldown + Debounce → GameState mutation
    │
    ▼
GameState.tick()  ──►  Gravity, Line Clear, Score, Level
    │
    ▼
Pygame Renderer + OpenCV Overlay
```

The gesture pipeline runs at **~60 FPS** with a sliding window smoother to eliminate jitter from noisy landmark data.

---

## 📊 Gesture Logic

### Zone-based Movement
The screen is divided into 3 horizontal zones based on the index finger tip (landmark 8):

```
|← 30% →|←── 40% ──→|← 30% →|
 MOVE_RIGHT   NONE   MOVE_LEFT
```

### State-machine Rotation
Rotation uses a **FIST → OPEN** transition to prevent accidental triggers:
- FIST detected → record state
- OPEN hand detected after FIST → trigger ROTATE

### Hard Drop Guard
Hard drop requires holding a fist for **2.5 seconds** — prevents accidental drops while transitioning between gestures.

---

## 🧪 Test Coverage

```bash
pytest tests/ -v --tb=short
```

| Test File | Coverage |
|---|---|
| `test_board.py` | Grid init, collision detection, line clearing, game-over |
| `test_piece.py` | All 7 tetrominoes, SRS rotation, PieceBag 7-bag system |
| `test_gesture.py` | Live gesture detection (requires webcam) |

---

## 🛠️ Extending the Project

### Add ML-based Gesture Classifier
Replace the rule-based classifier in `gesture_classifier.py` with a trained model:

```python
# In gesture_classifier.py
import pickle
model = pickle.load(open("models/gesture_model.pkl", "rb"))

def classify(self, landmarks) -> str:
    features = self._extract_features(landmarks)
    return model.predict([features])[0]
```

### Collect Training Data
Use `data/` folder to store labeled gesture samples and train a custom classifier.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
Built with ❤️ using Python · MediaPipe · Pygame · OpenCV
</div>