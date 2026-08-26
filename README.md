# ♟ Gambit

Gambit is a chess engine I'm building from scratch in **C++**.

The main goal isn't just to make a chess game that works. I want to understand how the different parts of a chess engine actually work — from basic piece movement and check detection all the way to move generation and eventually AI.

I'm building it step by step instead of using an existing chess engine like Stockfish.

## Current Progress

So far, I've implemented:

* Chess board and initial setup
* Move representation
* Pawn movement
* Knight movement
* Bishop movement
* Rook movement
* Queen movement
* King movement
* Check detection
* Attack detection for different pieces
* King escape validation
* Temporary board-state changes for checking whether a move is legal
* A cleaner console-based chessboard

The engine is still far from finished, but the basic structure is starting to take shape.

## What's Next?

The next major part is handling situations where the King is in check.

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
No possible move?
      ↓
Checkmate
```

After that, I'll work on the remaining chess rules such as:

* Castling
* En passant
* Pawn promotion
* Stalemate
* Draw conditions
* Move history

## Future Plans

Once the basic chess engine is complete, I want to take Gambit further.

Some things I have in mind:

**Game modes**

* Bullet
* Blitz
* Rapid
* Classical

**Chess AI**

I eventually want to build the AI myself instead of simply connecting Gambit to Stockfish. This will involve things like:

* Minimax
* Alpha-Beta pruning
* Move ordering
* Position evaluation
* Search optimization

The long-term goal is to see how strong I can actually make the engine.

## Why I'm Building This

This started as an OOP project, but it's gradually becoming much more than that.

While working on Gambit, I'm getting to deal with things like:

* Object-oriented design
* Algorithms
* Recursion
* Game-state management
* Move generation
* Search algorithms
* Performance optimization

And honestly, a lot of the interesting part is figuring out **why something doesn't work**, debugging it, and then improving the design.

## Tech Stack

* C++
* OOP
* STL
* Git & GitHub

## Project Structure

```text
Gambit/
│
├── main.cpp
├── Board.h
├── Board.cpp
├── Move.h
├── Move.cpp
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
└── README.md
```

## Current Status

🚧 **Work in Progress**

Gambit is being developed alongside college, so the project is intentionally being built over time rather than rushed.

The current version is still a console-based chess engine. Once the core engine becomes stable, I'll look into building a proper UI around it.

---

### Built by

**Jaivardhan Singh**
B.Tech CSE — BIT Mesra

This is a project I'm building to learn, experiment, break things, fix them, and eventually see how far I can take a chess engine built from scratch.
