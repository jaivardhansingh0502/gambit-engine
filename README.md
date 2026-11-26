# ♟️ Gambit — Chess Engine

<p align="center">
  <img src="https://img.shields.io/badge/C%2B%2B-17-00599C?style=for-the-badge&logo=cplusplus&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.15-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Status-Playable-16A34A?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Engine-Built%20From%20Scratch-16A34A?style=for-the-badge" />
</p>

<p align="center">
  <strong>A desktop chess engine built from scratch in C++ with a Python AI and Tkinter interface.</strong>
</p>

Gambit is a chess engine built from the ground up — combining a C++17 rules, move-generation, and state engine with a Python search AI and an interactive Tkinter desktop GUI.

---

## 🚀 Features

### C++ Chess Engine

- [x] 8×8 board representation & full piece movement validation
- [x] Legal move generation & king safety / check detection
- [x] Checkmate, stalemate, and insufficient material draw detection
- [x] Castling (kingside & queenside), en passant, and pawn promotion (`q`/`r`/`b`/`n`)
- [x] Board-state save & restore stack (`UNDO_MOVE`, `NEW_GAME`)
- [x] Line-based stdin/stdout protocol (`GET_MOVES`, `MAKE_MOVE`, `UNDO_MOVE`, `NEW_GAME`)

### Chess AI & Evaluation

- [x] Material evaluation + Knight and Pawn piece-square tables (`evaluation.py`)
- [x] Minimax search with Alpha-Beta pruning
- [x] Capture/promotion move ordering (including root move ordering)
- [x] Quiescence search with check evasion handling
- [x] Mate-distance scoring (prefers faster forced mates)
- [x] Configurable search depth (`Easy` / `Medium` / `Hard`)

### Python Tkinter Interface

- [x] Interactive graphical chess board with algebraic coordinates
- [x] Legal move, selected square, last move, and king-in-check highlighting
- [x] Clickable modal pawn promotion dialog (`♕`, `♖`, `♗`, `♘`)
- [x] Turn, AI thinking, check, checkmate, stalemate, and draw status banner
- [x] Move history panel, `Undo Move`, `New Game`, and `AI Level` selector
- [x] Thread-safe background engine communication & clean shutdown

---

## 🧠 Architecture

```text
   Python Tkinter GUI (ui.py)
               │
               ▼
      Python AI (ai.py) ──► Evaluation (evaluation.py)
               │
               ▼ (stdin / stdout)
   C++ Chess Engine (gambit.exe)
      ├── Move Generation & Legality
      ├── Special Moves (Castling, En Passant, Promotion)
      └── Game State Stack & Termination Detection
```

---

## 🗂️ Project Structure

```text
Chess/
├── Board.h / Board.cpp
├── Move.h / Move.cpp
├── Pawn.h / Pawn.cpp
├── Knight.h / Knight.cpp
├── Bishop.h / Bishop.cpp
├── Rook.h / Rook.cpp
├── Queen.h / Queen.cpp
├── King.h / King.cpp
├── Evaluation.h / Evaluation.cpp
├── main.cpp
├── ai.py
├── evaluation.py
├── ui.py
├── tests/
│   ├── test_engine.py
│   ├── test_ai.py
│   └── test_ui_logic.py
├── DEVELOPMENT_LOG.md
└── README.md
```

---

## 🛠️ Build, Run & Test

### 1. Build the C++ Engine

```bash
g++ -std=c++17 -O2 main.cpp Board.cpp Move.cpp Pawn.cpp Knight.cpp Bishop.cpp Rook.cpp Queen.cpp King.cpp Evaluation.cpp -o gambit.exe
```

### 2. Launch the Desktop GUI

```bash
python ui.py
```

### 3. Run the Automated Test Suite

```bash
python -m unittest discover -s tests -v
```

---

## 📌 Current Status

Gambit is playable end-to-end as a Human (White) vs AI (Black) desktop chess application, backed by an automated `unittest` suite covering the C++ protocol/rules engine, AI search, and Tkinter UI logic. See [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) for the milestone history.

♟️ One move at a time.
