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
- [x] Checkmate, stalemate, insufficient material, 50-move rule, and threefold repetition draw detection
- [x] Castling (kingside & queenside), en passant, and pawn promotion (`q`/`r`/`b`/`n`)
- [x] FEN import/export (`GET_FEN`, `SET_FEN`) and Board-state stack (`UNDO_MOVE`, `NEW_GAME`)
- [x] High-speed C++17 search (`BEST_MOVE` with Built-in Opening Book, Negamax PVS + Aspiration Windows, Null-Move Pruning, Late Move Reductions, Check Extensions, Quiescence + Delta Pruning, 64-bit Zobrist TT, MVV-LVA, Killer Moves, and History Heuristic)
- [x] Tapered middlegame/endgame positional evaluation (King safety pawn shield, passed/doubled/isolated pawns, knight outposts, rook open files & 7th rank, bishop pair)
- [x] Line-based stdin/stdout protocol (`GET_MOVES`, `MAKE_MOVE`, `UNDO_MOVE`, `NEW_GAME`, `EVALUATE`, `GET_FEN`, `SET_FEN`, `BEST_MOVE`, `ANALYZE_MOVE`)

### Chess AI & Evaluation

- [x] Material evaluation + positional piece-square tables (`Evaluation.cpp` / `evaluation.py`)
- [x] Live Position Evaluation Panel (advantage bar, material breakdown, C++ eval vs positional eval)
- [x] Configurable search difficulty (`Easy (Depth 2)` / `Medium (Depth 4)` / `Hard (Depth 6)`)

### Python Tkinter Interface

- [x] Interactive graphical chess board with algebraic coordinates, drag-and-drop, click-to-move, **Premoves**, right-click square highlights & analysis arrows, and slower smooth AI move animations
- [x] Selectable board themes (`Classic Green`, `Walnut Wood`, `Slate Blue`, `Tournament Charcoal`) & keyboard shortcuts (`←`/`→`, `Home`/`End`, `F`, `H`, `M`, `Esc`)
- [x] Legal move, selected square, last move, king-in-check highlighting, and `💡 Hint` best-move arrow
- [x] Clickable Standard Algebraic Notation (`SAN`) move history, **Live ECO Opening Name Banner**, **Post-Game Blunder Review (`!`, `?!`, `?`, `??`) & Accuracy %**, evaluation swing graph, captured pieces tray, and `🔊` sound toggle
- [x] Player vs AI (`White`/`Black`/`Random`, 30+ built-in ECO openings) & Player vs Player modes with live chess clocks (`Bullet`/`Blitz`/`Rapid`), `⇅ Flip`, `Resign`, `½ Draw` offer, FEN import, and PGN export
- [x] Animated `Back` / `Next` / `Live` move review without unfair undo
- [x] Thread-safe background engine communication & clean shutdown

---

## 🧠 Architecture

```text
   Python Tkinter GUI (ui.py + chess_utils.py)
               │
               ▼
      Engine Bridge (ai.py) ──► Evaluation Breakdown (evaluation.py)
               │
               ▼ (stdin / stdout)
   C++ Chess Engine (gambit.exe)
      ├── Move Generation, Legality & Special Moves
      ├── Alpha-Beta + Quiescence + Zobrist TT Search (Search.cpp)
      └── FEN, Position History, Draw Rules & Evaluation (Board.cpp / Evaluation.cpp)
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
├── Search.h / Search.cpp
├── main.cpp
├── ai.py
├── chess_utils.py
├── evaluation.py
├── ui.py
├── tests/
│   ├── test_chess_utils.py
│   ├── test_engine.py
│   ├── test_ai.py
│   ├── test_evaluation.py
│   └── test_ui_logic.py
├── DEVELOPMENT_LOG.md
└── README.md
```

---

## 🛠️ Build, Run & Test

### 1. Build the C++ Engine

```bash
g++ -std=c++17 -O2 main.cpp Board.cpp Move.cpp Pawn.cpp Knight.cpp Bishop.cpp Rook.cpp Queen.cpp King.cpp Evaluation.cpp Search.cpp -o gambit.exe
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

Gambit is playable end-to-end as both Player vs AI (`White`/`Black`/`Random`) and Player vs Player desktop chess application powered by a compiled C++17 search and rules engine, backed by a 41-test `unittest` suite covering C++ rules/search/openings/FEN/draws, SAN/PGN/review utilities, evaluation, AI, and Tkinter GUI workflows. See [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) for the milestone history.

♟️ One move at a time.
