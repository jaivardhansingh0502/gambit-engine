# ♟️ Gambit — Chess Engine

<p align="center">
  <img src="https://img.shields.io/badge/C%2B%2B-17-00599C?style=for-the-badge&logo=cplusplus&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Status-In%20Development-F59E0B?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Engine-Built%20From%20Scratch-16A34A?style=for-the-badge" />
</p>

<p align="center">
  <strong>A chess engine built from scratch in C++ with a Python interface.</strong>
</p>

Gambit is my ongoing project to understand how chess engines work by building one from the ground up — from board representation and move validation to legal move generation, king safety, evaluation, and eventually AI.

---

## 🚀 Current Progress

### Chess Engine

- [x] 8×8 board representation
- [x] All piece movement and validation
- [x] Check detection
- [x] Checkmate & stalemate
- [x] Legal move generation
- [x] Castling
- [x] En passant
- [x] Pawn promotion
- [x] Temporary board-state simulation
- [x] Board-state save & restore

### Python Interface

- [x] Tkinter graphical board
- [x] Click-based piece selection
- [x] Legal move highlighting
- [x] Board coordinates
- [x] Turn indicator
- [x] Last-move highlighting
- [x] Move history
- [x] New Game
- [x] C++ ↔ Python communication

### Evaluation

- [x] Basic material evaluation
- [x] Knight piece-square table
- [x] Pawn piece-square table

---

## 🧠 Architecture

```text
        Python GUI
            │
            ▼
     C++ Chess Engine
            │
    ┌───────┴────────┐
    ▼                ▼
Move Generation   Game State
    │
    ▼
Position Evaluation
    │
    ▼
   Search
    │
    ▼
   Chess AI

The C++ engine handles chess rules, board state, and legal moves, while Python currently handles the interface and evaluation/AI layer.

🗂️ Project Structure
Gambit/
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
└── README.md
🛠️ Tech Stack
C++17
Python
OOP
Data Structures & Algorithms
Tkinter
Git & GitHub
MSYS2 / MinGW
uv
📈 Roadmap
Chess & Engine
 Core chess rules
 Legal move generation
 Special moves
 Basic evaluation
 Draw conditions
 Improved position evaluation
 Minimax
 Alpha-Beta pruning
 Move ordering
 Transposition tables
Interface
 Interactive chess board
 Move history
 New Game
 Check/Checkmate indicators
 Promotion UI
 Chess clock
📌 Current Status

Gambit is actively under development.

The chess rules and legality system are now functional, with an interactive Python interface connected to the C++ engine.

The next major step is implementing search and stronger position evaluation to turn Gambit into an actual chess-playing engine.

♟️ One move at a time.
