# Gambit Chess Engine — Development Log

Repository: `https://github.com/jaivardhansingh0502/gambit-engine`  
Branch: `main`  
Baseline Commit: `b070b5e` (*Temporary Move Removed*)

---

## Milestone Plan

1. **Milestone 1 — Baseline Stabilization & Thread-Safe Human-vs-AI Integration**
   - Stabilize the `ui.py` ↔ `ai.py` integration, serialize engine I/O with a lock, keep UI state mutations on the Tkinter main thread, prevent shutdown race errors, and gate verbose per-node search logging in `ai.py`.
2. **Milestone 2 — Fix C++ Engine Promotion Bug & Add Automated Engine/Protocol Tests**
   - Fix `main.cpp` `MAKE_MOVE` parsing so 5-character promotion moves (e.g., `e7e8n`) preserve the promotion piece, recompile `gambit.exe`, and add `tests/test_engine.py` covering protocol commands, castling, en passant, promotions, checkmate, stalemate, and insufficient material.
3. **Milestone 3 — GUI Interaction, Promotion Dialog & Game-State Indicators**
   - Replace text-prompt promotion with a clickable piece-selection dialog, highlight the king square when in check, add an Undo Move button, and improve game-over presentation.
4. **Milestone 4 — AI Search Depth Control, Side/Turn Polish & AI Tests**
   - Add configurable AI search depth in the UI, improve engine/AI turn handling and `tests/test_ai.py` (mate-in-1 detection, capture preference, and engine state preservation).
5. **Milestone 5 — Final Stability Testing, Documentation & Cleanup**
   - Update `README.md` with accurate architecture, build, run, and test instructions, run the full test suite, and verify a clean repository state.

---

## Milestone 1 — Baseline Stabilization & Thread-Safe Human-vs-AI Integration

- **Status:** Completed
- **Commit:** `ae1edd5`
- **Changes Implemented:**
  - `ai.py`: Added `verbose=False` parameter to `send_move_to_engine()` and `AI.__init__()` so minimax/quiescence search no longer floods stdout on every node while preserving optional debug output.
  - `ui.py`:
    - Integrated `AI`, `get_position`, and `send_move_to_engine` cleanly into `GambitUI`.
    - Added `self.engine_lock` (`threading.Lock`) to serialize all subprocess stdin/stdout communication.
    - Added `self.closing` guard and `_handle_move_error()` to prevent background threads from raising Tkinter error dialogs during window shutdown.
    - Moved `move_history` and `last_move` updates into `update_position()` / `_apply_new_game_state()` on the Tkinter main thread.
    - Removed redundant `get_position()` call between `process_human_move()` and `process_ai_turn()` and kept `engine_busy=True` continuously across the human → AI turn transition.
- **Files Modified:**
  - `ai.py`
  - `ui.py`
  - `DEVELOPMENT_LOG.md`
- **Tests Performed:**
  - `python -m py_compile ai.py evaluation.py ui.py` — Passed.
  - AI smoke test (`e2e4` followed by `AI.find_best_move` and engine state verification) — Passed (`best=b8c6`, `nodes=1790`, engine turn/moves preserved).
  - Headless `GambitUI` smoke test (initial position load → `make_move('e2e4')` → AI reply → `new_game()` → `close()`) — Passed.

---

## Milestone 2 — Fix C++ Engine Promotion Bug & Add Automated Engine/Protocol Tests

- **Status:** Completed
- **Commit:** `780a14d`
- **Changes Implemented:**
  - `main.cpp`: Fixed `MAKE_MOVE` parsing (`moveString.substr(2)` instead of `moveString.substr(2, 2)`) so 5-character promotion moves (e.g., `a7b8n`) preserve the promotion piece, and added input length/promotion-character validation returning `MOVE_INVALID` on malformed input.
  - Recompiled `gambit.exe` with `g++ -std=c++17 -O2` (note: `*.exe` is gitignored).
  - `tests/test_engine.py`: Added 7 unit tests covering initial board/protocol, invalid & malformed moves, `UNDO_MOVE` & `NEW_GAME`, kingside & queenside castling, en passant capture, under-promotion preservation, and checkmate/`GAME_OVER` guard.
- **Files Modified:**
  - `main.cpp`
  - `tests/test_engine.py`
  - `DEVELOPMENT_LOG.md`
- **Tests Performed:**
  - `g++ -std=c++17 -O2 main.cpp Board.cpp Move.cpp Pawn.cpp Knight.cpp Bishop.cpp Rook.cpp Queen.cpp King.cpp Evaluation.cpp -o gambit.exe` — Passed.
  - `python -m unittest discover -s tests -v` — 7 tests passed in 0.104s.

---

## Milestone 3 — GUI Interaction, Promotion Dialog & Game-State Indicators

- **Status:** Completed
- **Commit:** `52c9011`
- **Changes Implemented:**
  - `ui.py`:
    - Replaced `simpledialog.askstring` in `choose_promotion()` with a clickable modal `tk.Toplevel` dialog (`♕ Queen`, `♖ Rook`, `♗ Bishop`, `♘ Knight`).
    - Added king-in-check / checkmate square highlighting (`#E06C75`) via `find_king_square()`.
    - Added `Undo Move` button (`undo_last_turn()`, `_process_undo()`, `_apply_undo_state()`) and `_update_controls()` so human players can cleanly undo turns without breaking AI turn parity.
    - Extracted `square_to_notation()`, `find_king_square()`, `get_promotion_map()`, `format_status_text()`, and `get_board_geometry()` helpers, removing duplicated geometry math and fixing status label spacing/coloring.
  - `tests/test_ui_logic.py`: Added 6 unit & headless UI integration tests covering UI helper functions and the full move → AI reply → undo → new game flow.
- **Files Modified:**
  - `ui.py`
  - `tests/test_ui_logic.py`
  - `DEVELOPMENT_LOG.md`
- **Tests Performed:**
  - `python -m unittest discover -s tests -v` — 13 tests passed in 0.826s.

---

## Milestone 4 — AI Search Depth Control, Search Polish & AI Tests

- **Status:** Completed
- **Changes Implemented:**
  - `ai.py`:
    - Added configurable `depth=2` parameter to `AI.find_best_move()`.
    - Applied `order_moves()` at the root move loop in `find_best_move()` and respected `self.verbose` in `send_move_to_engine()`.
    - Added mate-distance scoring bonuses in `minimax()` (`100000 + depth * 10`) and `quiescence_search()` (`100000 + remaining_depth`) so the AI always prefers faster forced checkmates.
  - `ui.py`:
    - Added an `AI Level` selector (`Easy (Depth 1)`, `Medium (Depth 2)`, `Hard (Depth 3)`) via `AI_DIFFICULTY_DEPTHS` and `get_ai_depth()`, disabled while the engine is busy.
    - Closed subprocess `stdin`/`stdout` pipes cleanly in `close()`.
  - `tests/test_ai.py`: Added 4 AI unit tests verifying configurable search depth, engine state preservation after search, Scholar's Mate & Fool's Mate mate-in-1 detection, and alpha-beta node reduction vs minimax.
  - `tests/test_ui_logic.py`: Added assertions covering `get_ai_depth()` default and updated difficulty selection.
- **Files Modified:**
  - `ai.py`
  - `ui.py`
  - `tests/test_ai.py`
  - `tests/test_ui_logic.py`
  - `DEVELOPMENT_LOG.md`
- **Tests Performed:**
  - `python -m unittest discover -s tests -v` — 17 tests passed in 1.249s.
