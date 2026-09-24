# ♟️ Gambit Engine

> A chess engine built from scratch in C++.

Gambit is my ongoing project to understand how chess engines actually work by building one from the ground up — starting with board representation and piece movement, and gradually developing the complete rules and logic required for a legal chess game.

---

## 🚀 Current Progress

Gambit currently has a working chess rules and legality foundation.

### Implemented

- ♟️ 8×8 board representation
- ♙ Pawn movement and captures
- ♘ Knight movement
- ♗ Bishop movement
- ♖ Rook movement
- ♕ Queen movement
- ♔ King movement
- 🛡️ Move validation
- ⚔️ Check detection
- 👑 King safety validation
- ♔ King escape detection
- 🛡️ Piece-based King-saving logic
- ♚ Checkmate detection
- 🤝 Stalemate detection
- 🏰 Kingside castling
- 🏰 Queenside castling
- 🔄 Castling for both White and Black
- 📜 King and Rook movement-history tracking
- 💻 Console-based board display
- 🎮 Turn-based gameplay

---

## 🧠 How Gambit Validates a Move

A chess move is more than simply moving a piece from one square to another.

Gambit follows this general flow:

    Player Input
         │
         ▼
      Move Object
         │
         ▼
    Movement Valid?
         │
         ▼
    Simulate Move
         │
         ▼
    King in Check?
       /       \
     YES       NO
      │         │
      ▼         ▼
   Illegal    Legal
      │         │
      └────┬────┘
           ▼
      Restore / Update
         Board State

Temporary board states are used while checking King safety, allowing Gambit to test hypothetical moves without permanently changing the position.

---

## ⚔️ King Safety

Gambit can currently detect attacks from:

    Pawn
    Knight
    Bishop
    Rook
    Queen
    King

King safety is then used by several higher-level rules:

    Check
      ↓
    Can the King escape?
      ↓
    Can another piece save the King?
      ↓
    No legal response?
      ↓
    Checkmate

The same legal-move system is also used to distinguish checkmate from stalemate.

---

## 🏰 Castling

All four castling cases are implemented:

    White Kingside     e1 → g1
    White Queenside    e1 → c1

    Black Kingside     e8 → g8
    Black Queenside    e8 → c8

The corresponding Rook is moved automatically as part of the castling move.

Gambit checks:

- Whether the King has previously moved
- Whether the corresponding Rook has previously moved
- Whether the required squares are empty
- Whether the King is currently in check
- Whether the King crosses an attacked square
- Whether the destination square is attacked

Movement history is stored separately, so moving a King or Rook away and then returning it does not incorrectly restore castling rights.

---

## ♟️ Board Representation

The internal board is represented using:

    char board[8][8];

White pieces use uppercase characters:

    P  R  N  B  Q  K

Black pieces use lowercase characters:

    p  r  n  b  q  k

Empty squares are represented internally using:

    ' '

The board uses zero-based array indexing:

    Row 0 → Rank 8
    Row 1 → Rank 7
    Row 2 → Rank 6
    Row 3 → Rank 5
    Row 4 → Rank 4
    Row 5 → Rank 3
    Row 6 → Rank 2
    Row 7 → Rank 1

Columns map to:

    0 → a
    1 → b
    2 → c
    3 → d
    4 → e
    5 → f
    6 → g
    7 → h

---

## 🗂️ Project Structure

    Gambit/
    │
    ├── Board.h
    ├── Board.cpp
    ├── Move.h
    ├── Move.cpp
    │
    ├── Pawn.h
    ├── Pawn.cpp
    ├── Knight.h
    ├── Knight.cpp
    ├── Bishop.h
    ├── Bishop.cpp
    ├── Rook.h
    ├── Rook.cpp
    ├── Queen.h
    ├── Queen.cpp
    ├── King.h
    ├── King.cpp
    │
    └── main.cpp

The project is intentionally being developed incrementally so that the underlying chess logic is understood and implemented rather than hidden behind an existing engine or library.

---

## 🛠️ Tech Stack

- C++
- Object-Oriented Programming
- Standard C++ Libraries
- Git & GitHub
- MSYS2 / MinGW

---

## 📈 Roadmap

### Chess Rules

- [x] Basic piece movement
- [x] Move validation
- [x] Check detection
- [x] King safety
- [x] Checkmate
- [x] Stalemate
- [x] Kingside castling
- [x] Queenside castling
- [ ] Pawn promotion
- [ ] En passant
- [ ] Draw conditions

### Engine Development

- [ ] Complete move generation
- [ ] Improved move history
- [ ] Better board-state management
- [ ] Position evaluation
- [ ] Search algorithms
- [ ] Alpha-Beta pruning
- [ ] Difficulty levels
- [ ] Engine vs Engine testing

### Future

- 🤖 Chess AI
- ♟️ Stronger position evaluation
- 🔍 Search optimization
- 🎮 Better user interface
- 🌐 Possible chess-platform-style interface

---

## 🌱 Why Gambit?

Gambit is more than a chess project for me. It is a long-term C++ project where I am applying concepts from DSA, OOP, algorithms, debugging, and problem solving to a real system.

The long-term direction is:

    Data Structures
          ↓
      Game Logic
          ↓
    Move Generation
          ↓
    Position Evaluation
          ↓
       Search
          ↓
     Chess AI

The engine is being built one system at a time, with each feature tested and integrated before moving to the next stage.

---

## 📌 Current Status

**Gambit is actively under development.**

The chess rules and legality system now form the foundation for the next stage of the project: turning Gambit from a chess rules engine into an actual chess-playing engine.

♟️ **One move at a time.**
