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
- [x] **Perft(1..4) Rules Verification (`PERFT`)** & **Standard UCI Protocol** (`uci`, `isready`, `ucinewgame`, `position startpos/fen moves ...`, `go depth/movetime/wtime/btime`, `quit`) compatible with Arena / CuteChess
- [x] Line-based native stdin/stdout protocol (`GET_MOVES`, `MAKE_MOVE`, `UNDO_MOVE`, `NEW_GAME`, `EVALUATE`, `GET_FEN`, `SET_FEN`, `BEST_MOVE`, `ANALYZE_MOVE`, `PERFT`)

### Chess AI & Evaluation

- [x] Material evaluation + positional piece-square tables (`Evaluation.cpp` / `evaluation.py`)
- [x] **Real-Time AI+ Position Evaluation Panel** (`AI+ LIVE` depth-4 search advantage & mate indicator, sleek advantage bar, live momentum graph, side-by-side material balance, and C++ material comparison synced across live play & history replay)
- [x] Configurable search difficulty (`Easy (Depth 2)` / `Medium (Depth 4)` / `Hard (Depth 6)`)

### Python Tkinter Interface

- [x] Interactive graphical chess board with algebraic coordinates, drag-and-drop, click-to-move, **Premoves**, right-click square highlights & analysis arrows, and slower smooth AI move animations
- [x] Selectable **Board Themes** (`Classic Green`, `Walnut Wood`, `Slate Blue`, `Tournament Charcoal`), **Sidebar Color Themes** (`Obsidian Emerald`, `Midnight Indigo`, `Warm Espresso`, `Arctic Light`), toggleable **Vertical Eval Bar Beside the Board**, and keyboard shortcuts (`←`/`→`, `Home`/`End`, `F`, `H`, `M`, `Esc`)
- [x] Legal move, selected square, last move, king-in-check highlighting, and `💡 Hint` best-move arrow
- [x] Clickable Standard Algebraic Notation (`SAN`) move history, **Live ECO Opening Name Banner**, **▶ Play Here** branching vs AI from any reviewed move, **Post-Game Blunder Review (`!`, `?!`, `?`, `??`) & Accuracy %**, evaluation swing graph, captured pieces tray with **Material Advantage Badges (`+3`)**, and cross-platform `🔊` sound toggle
- [x] Player vs AI (`White`/`Black`/`Random`, 30+ built-in ECO openings) & Player vs Player modes with live chess clocks (`Bullet`/`Blitz`/`Rapid`), `⇅ Flip`, `Resign`, `½ Draw` offer, FEN import, **PGN Import & Export**, and **Auto-Saved Game Library & W-D-L Stats (`📚`)**
- [x] Animated `Back` / `Next` / `Live` move review without unfair undo
- [x] **Persistent User Preferences (`settings.json`)** for board & sidebar themes, eval bar visibility, sound mute, AI difficulty, and time control (including **Custom `M+I` time controls** alongside `Bullet`/`Blitz`/`Rapid` presets)
- [x] **Cross-Platform Standalone Desktop App Packaging (`build_app.py` + GitHub Actions):** Builds a zero-dependency Windows `GambitChess.exe` (with statically linked `gambit.exe`) and macOS `GambitChess.app` / `.dmg` (universal `arm64`/`x86_64` `gambit` engine + Aqua Tk & sound compatibility) alongside silent `.vbs` and desktop shortcut launchers
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
├── build_app.py
├── .github/workflows/build-releases.yml
├── assets/
│   └── gambit.ico
├── Launch Gambit Chess.vbs
├── install_desktop_shortcut.ps1
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

## 🛠️ Build, Run, Package & Test

### 1. Download Ready-to-Run Desktop Apps (Windows & macOS)

- **GitHub Actions Builds:** Every push to `main` (and version tag `v*`) automatically builds `GambitChess-Windows.zip` (`GambitChess.exe`) and `GambitChess-macOS` (`GambitChess.app` + `.dmg`) in the repository's **Actions** / **Releases** tab — no Python or compiler needed on the target laptop.

### 2. Build Standalone App Locally (Windows or macOS)

```bash
pip install pyinstaller
python build_app.py
```

Outputs `dist/GambitChess.exe` + `dist/GambitChess-Windows.zip` on Windows (with statically linked `gambit.exe`) or `dist/GambitChess.app` + `dist/GambitChess-macOS.zip` / `.dmg` on macOS.

### 3. Build & Run From Source

```bash
g++ -std=c++17 -O2 -static -static-libgcc -static-libstdc++ main.cpp Board.cpp Move.cpp Pawn.cpp Knight.cpp Bishop.cpp Rook.cpp Queen.cpp King.cpp Evaluation.cpp Search.cpp -o gambit.exe
python ui.py
```

Or on Windows, double-click `Launch Gambit Chess.vbs` to run without a console window, or run `powershell -ExecutionPolicy Bypass -File install_desktop_shortcut.ps1` to create a Windows Desktop shortcut with Gambit's icon.

### 4. Run the Automated Test Suite

```bash
python -m unittest discover -s tests -v
```

---

## 📌 Current Status

Gambit is playable end-to-end as both Player vs AI (`White`/`Black`/`Random`) and Player vs Player desktop chess application powered by a Perft-verified, UCI-compatible C++17 search and rules engine, backed by a 51-test `unittest` suite covering C++ rules/Perft/UCI/search/openings/FEN/draws, SAN/PGN import & export, game library stats, review/themes/settings/icon utilities, evaluation, AI, and Tkinter GUI workflows. See [DEVELOPMENT_LOG.md](DEVELOPMENT_LOG.md) for the milestone history.

♟️ One move at a time.
