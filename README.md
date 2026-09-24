# ♟ Gambit — Chess Engine

Gambit is a chess engine that I am building from scratch in **C++** to strengthen my understanding of C++, OOP, algorithms, and software architecture.

The goal isn't just to make a chess game that works. I want to understand how the different parts of a chess engine actually work — from basic piece movement and check detection to move validation, game-state management, and eventually chess AI.

I'm building it step by step instead of using an existing chess engine like Stockfish.

---

## 🚧 Current Progress

### Board & Pieces

- [x] Chess board representation
- [x] Initial board setup
- [x] Pawn
- [x] Knight
- [x] Bishop
- [x] Rook
- [x] Queen
- [x] King

### Movement

- [x] Basic movement validation
- [x] Capture validation
- [x] Path obstruction checking
- [x] Pawn movement and captures
- [x] Turn-based movement
- [x] Move representation

### King Safety & Game State

- [x] Check detection
- [x] Attack detection for different pieces
- [x] King escape validation
- [x] Piece-based king-saving validation
- [x] Temporary board-state simulation
- [x] Checkmate detection
- [x] Legal move detection
- [x] Stalemate detection

### Special Moves

- [x] Kingside castling
- [x] Queenside castling
- [x] White castling
- [x] Black castling
- [x] Castling rights tracking
- [x] King movement restriction
- [x] Rook movement restriction
- [x] Castling attack validation

### Terminal Interface

- [x] Unicode chess pieces
- [x] ANSI colored board
- [x] Board redraw after moves
- [x] Interactive move input

### Project Structure

- [x] Separated classes into `.h` and `.cpp` files
- [x] Modular piece-based architecture
- [x] Git/GitHub version control

---

## 🛠️ Technologies

- C++
- Object-Oriented Programming
- STL
- Git & GitHub
- ANSI Escape Codes
- Unicode

---

## ♟️ How Gambit Handles King Safety

One of the important parts of the engine is determining whether a move leaves the King vulnerable.

The engine uses temporary board-state changes to test possible positions before deciding whether a move is legal.

For example:

```text
King is in check
      ↓
Can the King escape?
      ↓
Can another piece capture the attacker?
      ↓
Can another piece block the attack?
      ↓
No legal move?
      ↓
Checkmate
