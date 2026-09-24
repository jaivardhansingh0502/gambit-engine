# ♟️ Gambit — Chess Engine

<p align="center">
  <img src="https://img.shields.io/badge/C%2B%2B-17-00599C?style=for-the-badge&logo=cplusplus&logoColor=white" />
  <img src="https://img.shields.io/badge/OOP-Designed-7C3AED?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Status-In%20Development-F59E0B?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Engine-Built%20From%20Scratch-16A34A?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Git-GitHub-181717?style=for-the-badge&logo=github" />
</p>

<p align="center">
  <strong>A chess engine built from scratch in C++.</strong>
</p>

<p align="center">
  Gambit is a learning-focused chess engine designed to understand<br>
  how chess engines actually work — from board representation and move<br>
  validation to king safety, game-state management, search, and eventually AI.
</p>

---

# ♟️ About Gambit

Gambit is a **C++ chess engine that I am building from scratch** to strengthen my understanding of:

- C++
- Object-Oriented Programming
- Data Structures & Algorithms
- Game-state management
- Algorithms and recursion
- Search algorithms
- Software architecture
- Debugging and problem solving

The goal isn't simply to create a chess game that works.

I want to understand what actually happens inside a chess engine.

Instead of connecting Gambit to an existing engine such as Stockfish, I'm implementing the core systems myself and building the engine step by step.

---

# 🧠 How Gambit Works

The long-term architecture of Gambit can be visualized as:

```mermaid
flowchart LR

    A["♟ Player Input"]
    B["Move Parser"]
    C["Move Validation"]
    D["King Safety"]
    E["Board State"]
    F["Game State"]
    G["Move Generation"]
    H["Position Evaluation"]
    I["Search"]
    J["🧠 Gambit AI"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J

    style A fill:#1e293b,color:#ffffff,stroke:#64748b
    style B fill:#2563eb,color:#ffffff,stroke:#60a5fa
    style C fill:#7c3aed,color:#ffffff,stroke:#a78bfa
    style D fill:#dc2626,color:#ffffff,stroke:#f87171
    style E fill:#0891b2,color:#ffffff,stroke:#22d3ee
    style F fill:#0f766e,color:#ffffff,stroke:#2dd4bf
    style G fill:#9333ea,color:#ffffff,stroke:#c084fc
    style H fill:#c026d3,color:#ffffff,stroke:#e879f9
    style I fill:#ea580c,color:#ffffff,stroke:#fb923c
    style J fill:#16a34a,color:#ffffff,stroke:#4ade80
