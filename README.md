# 🖐️ Finger Control Tetris

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-green?logo=google&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.5-red)
![OpenCV](https://img.shields.io/badge/OpenCV-4.9-blue?logo=opencv)

**Play Tetris using only your hand gestures — no keyboard, no controller.**  
Real-time hand detection powered by MediaPipe.

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

## 🚀 Quick Start

**Requirements:** Python 3.10+ · Webcam · Windows / macOS / Linux

```bash
# 1. Clone & install
git clone https://github.com/PattriraTnsg/finger-tetris.git
cd finger-tetris
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt

# 2. Run
python src/main.py
```
