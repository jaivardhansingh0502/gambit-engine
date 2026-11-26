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
- **Commit:** `59ed906`
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

---

## Milestone 5 — Final Stability Testing, Documentation & Project Cleanup

- **Status:** Completed
- **Commit:** `ab6076c`
- **Changes Implemented:**
  - `README.md`: Updated project documentation with current features, architecture diagram, project structure (including `tests/` and `DEVELOPMENT_LOG.md`), C++17 build instructions, desktop GUI launch command, and `unittest` suite instructions; fixed an unclosed code block in the Markdown.
  - Verified clean tracked repository file list via `git ls-files` (no untracked temporary files or binaries committed).
  - Recompiled `gambit.exe` and ran full syntax checks and test suite end-to-end.
- **Files Modified:**
  - `README.md`
  - `DEVELOPMENT_LOG.md`
- **Tests Performed:**
  - `g++ -std=c++17 -O2 main.cpp Board.cpp Move.cpp Pawn.cpp Knight.cpp Bishop.cpp Rook.cpp Queen.cpp King.cpp Evaluation.cpp -o gambit.exe` — Passed.
  - `python -m py_compile ai.py evaluation.py ui.py tests/test_engine.py tests/test_ai.py tests/test_ui_logic.py` — Passed.
  - `python -m unittest discover -s tests -v` — 17 tests passed in 1.321s.

---

## Milestone 6 — Game Mode Selection (PvP / PvAI) & Position Evaluation Panel

- **Status:** Completed
- **Commit:** `e59366c`
- **Changes Implemented:**
  - `main.cpp`: Added `EVALUATE` command calling `evaluation.evaluateBoard(chessboard.getBoard())` (`Evaluation.cpp` material-only score) and recompiled `gambit.exe`.
  - `ai.py`: Added `get_engine_evaluation(engine)` to read `EVAL <score>` cleanly over the engine pipe.
  - `evaluation.py`: Added `analyze_material(board)` and `format_evaluation_summary(score, threshold=0.25)` for White/Black piece counts (Q/R/B/N/P, excluding kings), White-perspective material score, thresholded headline formatting, and natural-language material difference explanations.
  - `ui.py`:
    - Added Game Mode selection (`MODE_PVP`, `MODE_PVAI`) via `choose_game_mode()`, startup mode prompt, `New Game` mode switching, prominent mode banner (`mode_label`), mode-aware piece selection (`can_human_interact`, `is_own_piece`), PvP-safe AI gating, and mode-aware `Undo Move` (`get_undo_count`).
    - Added Position Evaluation Panel showing White-perspective headline (`White is better` / `Black is better` / `Position is equal`), visual advantage bar (`_draw_eval_bar`, `compute_advantage_ratio`), separate C++ Engine Eval (material-only `Evaluation.cpp`) and AI Search Eval (`evaluation.py` Material + Knight/Pawn PST), plus White/Black material counts and difference explanation updated after every move, undo, and reset under `self.engine_lock`.
  - `tests/test_engine.py`, `tests/test_evaluation.py`, `tests/test_ui_logic.py`: Added tests for `EVALUATE` command, material breakdown/captures/promotions/orientation, PvP manual play without AI, PvAI Black-only AI response, mode switching via `new_game`, and evaluation updates.
- **Files Modified:**
  - `main.cpp`
  - `ai.py`
  - `evaluation.py`
  - `ui.py`
  - `tests/test_engine.py`
  - `tests/test_evaluation.py`
  - `tests/test_ui_logic.py`
  - `DEVELOPMENT_LOG.md`
- **Tests Performed:**
  - `g++ -std=c++17 -O2 main.cpp Board.cpp Move.cpp Pawn.cpp Knight.cpp Bishop.cpp Rook.cpp Queen.cpp King.cpp Evaluation.cpp -o gambit.exe` — Passed.
  - `python -m py_compile ai.py evaluation.py ui.py tests/test_engine.py tests/test_ai.py tests/test_evaluation.py tests/test_ui_logic.py` — Passed.
  - `python -m unittest discover -s tests -v` — 24 tests passed in 2.017s.

---

## Milestone 7 — Modern Tkinter UI Overhaul, Inline Mode Switcher & Competitive AI

- **Status:** Completed
- **Commit:** `60570c1`
- **Changes Implemented:**
  - `evaluation.py`: Switched `evaluate_board()` to balanced centipawn `AI_PIECE_VALUES` (`P=100, N=320, B=330, R=500, Q=900`), added full piece-square tables (`PAWN_TABLE`, `KNIGHT_TABLE`, `BISHOP_TABLE`, `ROOK_TABLE`, `QUEEN_TABLE`, `KING_MIDDLE_TABLE`, `KING_END_TABLE`), bishop pair bonus (`+30` cp), and endgame king centralization, while preserving conventional `1/3/5/9` `PIECE_VALUES` for `analyze_material()`.
  - `ai.py`: Upgraded `AI` with iterative deepening (`depth` + optional `time_limit`), best-move transposition hint table (`best_move_table`), killer-move ordering (`killer_moves`), en passant capture ordering, and PST-delta quiet move ordering (`68.71%` alpha-beta node reduction vs minimax).
  - `ui.py`:
    - Redesigned Tkinter GUI with a modern dark slate theme (`THEME`), framed tournament board (`#EEEED2` / `#769656`), legal move dots & capture rings, and bold outlined solid piece glyphs.
    - Added an always-visible segmented Game Mode selector (`Player vs AI` / `Player vs Player`) directly in the sidebar (`select_mode_from_sidebar()`, `_refresh_mode_buttons()`) alongside dark-themed startup/promotion modals.
    - Upgraded default Medium AI difficulty to `Medium (Depth 3)` with a `2.0s` iterative-deepening budget (`Hard (Depth 4)` with `4.5s`, `Easy (Depth 1)` with `0.5s`) and formatted AI Positional Eval in pawns.
  - `tests/test_ai.py`, `tests/test_ui_logic.py`: Added `test_captures_hanging_queen`, sidebar mode-switching checks, and Medium depth/time-limit assertions.
- **Files Modified:**
  - `evaluation.py`
  - `ai.py`
  - `ui.py`
  - `tests/test_ai.py`
  - `tests/test_ui_logic.py`
  - `DEVELOPMENT_LOG.md`
- **Tests Performed:**
  - `python -m py_compile ai.py evaluation.py ui.py tests/test_engine.py tests/test_ai.py tests/test_evaluation.py tests/test_ui_logic.py` — Passed.
  - `python -m unittest discover -s tests -v` — 25 tests passed in 1.634s (68.71% Alpha-Beta node reduction).

---

## Milestone 8 — Resign Support (PvP & PvAI) and Animated Move History Replay

- **Status:** Completed
- **Commit:** `dcc0f86`
- **Changes Implemented:**
  - `ui.py`:
    - Removed the player-facing `Undo Move` button (`undo_last_turn()`, `get_undo_count()`) so players cannot take back moves during a game.
    - Added `🏳 Resign` (`resign_game()`, `RESIGNED_WHITE`, `RESIGNED_BLACK`) working in both `PvP` (active player resigns) and `PvAI` (human resigns), disabling further moves until `New Game`.
    - Added non-destructive move history navigation (`◀ Back`, `Next ▶`, `⏭ Live`) backed by `position_history`, `view_index`, `is_viewing_live()`, and smooth canvas piece animation (`_animate_move_step()`, `step_back()`, `step_forward()`, `jump_to_live()`), keeping evaluation and move-history highlight synchronized while blocking new moves during review.
  - `tests/test_ui_logic.py`: Updated tests to confirm Undo removal and verify animated Back/Forward replay, `jump_to_live()`, and `resign_game()` in both `PvAI` and `PvP`.
- **Files Modified:**
  - `ui.py`
  - `tests/test_ui_logic.py`
  - `DEVELOPMENT_LOG.md`
- **Tests Performed:**
  - `python -m py_compile ai.py evaluation.py ui.py tests/test_engine.py tests/test_ai.py tests/test_evaluation.py tests/test_ui_logic.py` — Passed.
  - `python -m unittest discover -s tests -v` — 25 tests passed in 2.819s.

---

## Milestone 9 — Chess Clock, Play as Black vs AI & Flip Board

- **Status:** Completed
- **Commit:** `87ba995`
- **Changes Implemented:**
  - `ui.py`:
    - Added selectable Chess Clocks (`TIME_CONTROLS`: `Untimed`, `Bullet (1+0)`, `Blitz (3+2)`, `Rapid (10+0)`) with Top/Bottom clock displays, active turn highlighting, low-time `<15s` warning, move increment (`_apply_increment`), live 100ms countdown (`_tick_clock`), and timeout termination (`TIMEOUT_WHITE`, `TIMEOUT_BLACK`).
    - Added Play as White / Black / Random in `PvAI` via `human_color`, `should_ai_move_for_turn()`, automatic AI opening move when human plays Black (`_maybe_start_ai_opening()`), and updated `can_human_interact()` & `format_status_text()`.
    - Added `⇅ Flip` board perspective toggle (`flip_board()`, `board_to_display_coords()`, `display_to_board_coords()`), updating board rendering, rank/file coordinates, mouse clicks, Back/Next animations, and Top/Bottom clock alignment.
  - `tests/test_ui_logic.py`: Added tests for clock formatting, coordinate flipping, White/Black AI turn helpers, and full headless integration test (`test_play_as_black_flip_board_and_clock_timeout`).
- **Files Modified:**
  - `ui.py`
  - `tests/test_ui_logic.py`
  - `DEVELOPMENT_LOG.md`
- **Tests Performed:**
  - `python -m py_compile ai.py evaluation.py ui.py tests/test_engine.py tests/test_ai.py tests/test_evaluation.py tests/test_ui_logic.py` — Passed.
  - `python -m unittest discover -s tests -v` — 26 tests passed in 3.171s.

---

## Milestone 10 — Inline Sidebar Time & Side Selectors and Laptop Screen Layout Fix

- **Status:** Completed
- **Changes Implemented:**
  - `ui.py`:
    - Added inline **Time** (`Untimed`, `Bullet (1+0)`, `Blitz (3+2)`, `Rapid (10+0)`) and **Side** (`White`, `Black`, `Random`) dropdown selectors directly in the sidebar (`on_sidebar_time_change()`, `on_sidebar_side_change()`) synchronized with `_apply_game_config()` and `_update_controls()`.
    - Fixed sidebar packing order by packing bottom controls (`action_frame`, `review_frame`, `settings_frame`) with `side="bottom"` before the `height=4` expandable `history_list`, preventing `Resign` and `New Game` buttons from clipping off 720p/768p laptop screens.
  - `tests/test_ui_logic.py`: Added `test_sidebar_time_and_side_selectors` and verified all sidebar controls fit cleanly inside `1280x680`.
- **Files Modified:**
  - `ui.py`
  - `tests/test_ui_logic.py`
  - `DEVELOPMENT_LOG.md`
- **Tests Performed:**
  - `1280x680` sidebar geometry check (`time_menu`, `side_menu`, `difficulty_menu`, `back_button`, `flip_button`, `resign_button`, `new_game_button` all within `sidebar h=713`) — Passed.
  - `python -m py_compile ai.py evaluation.py ui.py tests/test_engine.py tests/test_ai.py tests/test_evaluation.py tests/test_ui_logic.py` — Passed.
  - `python -m unittest discover -s tests -v` — 27 tests passed in 3.258s.
