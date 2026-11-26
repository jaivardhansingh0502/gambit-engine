import os
import sys
import tkinter as tk
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import ui


class GambitUIHelperTests(unittest.TestCase):
    def test_square_to_notation_and_notation_to_coords(self):
        self.assertEqual(ui.square_to_notation(0, 0), "a8")
        self.assertEqual(ui.square_to_notation(7, 4), "e1")
        self.assertEqual(ui.square_to_notation(3, 7), "h5")
        self.assertEqual(ui.notation_to_coords("a8"), (0, 0))
        self.assertEqual(ui.notation_to_coords("e1"), (7, 4))
        self.assertEqual(ui.notation_to_coords("h5"), (3, 7))

    def test_find_king_square(self):
        board = [["." for _ in range(8)] for _ in range(8)]
        board[7][4] = "K"
        board[0][6] = "k"
        self.assertEqual(ui.find_king_square(board, True), "e1")
        self.assertEqual(ui.find_king_square(board, False), "g8")

    def test_get_promotion_map(self):
        moves = ["a7a8q", "a7a8r", "a7a8b", "a7a8n", "e2e4"]
        promo_map = ui.get_promotion_map(moves)
        self.assertEqual(
            promo_map,
            {"q": "a7a8q", "r": "a7a8r", "b": "a7a8b", "n": "a7a8n"},
        )

    def test_format_status_text(self):
        text, _ = ui.format_status_text("NORMAL", False, True, game_mode=ui.MODE_PVAI)
        self.assertIn("AI thinking", text)

        text_pvp, _ = ui.format_status_text("NORMAL", False, True, game_mode=ui.MODE_PVP)
        self.assertNotIn("AI thinking", text_pvp)

        text, _ = ui.format_status_text("CHECK", True, False)
        self.assertEqual(text, "White to move — CHECK")

        text, _ = ui.format_status_text("CHECKMATE", True, False)
        self.assertEqual(text, "CHECKMATE — Black wins")

        text, _ = ui.format_status_text("STALEMATE", False, False)
        self.assertEqual(text, "STALEMATE — Draw")

        text, _ = ui.format_status_text("RESIGNED_WHITE", True, False)
        self.assertEqual(text, "White resigned — Black wins")

        text, _ = ui.format_status_text("RESIGNED_BLACK", False, False)
        self.assertEqual(text, "Black resigned — White wins")

        text, _ = ui.format_status_text("TIMEOUT_WHITE", True, False)
        self.assertEqual(text, "Time out — Black wins")

        text, _ = ui.format_status_text("TIMEOUT_BLACK", False, False)
        self.assertEqual(text, "Time out — White wins")

        text, _ = ui.format_status_text(
            "NORMAL", True, True, game_mode=ui.MODE_PVAI, human_color=ui.HUMAN_COLOR_BLACK
        )
        self.assertEqual(text, "White — AI thinking...")

    def test_mode_and_advantage_helpers(self):
        self.assertTrue(ui.can_human_interact(ui.MODE_PVP, True))
        self.assertTrue(ui.can_human_interact(ui.MODE_PVP, False))
        self.assertTrue(ui.can_human_interact(ui.MODE_PVAI, True, ui.HUMAN_COLOR_WHITE))
        self.assertFalse(ui.can_human_interact(ui.MODE_PVAI, False, ui.HUMAN_COLOR_WHITE))
        self.assertFalse(ui.can_human_interact(ui.MODE_PVAI, True, ui.HUMAN_COLOR_BLACK))
        self.assertTrue(ui.can_human_interact(ui.MODE_PVAI, False, ui.HUMAN_COLOR_BLACK))

        self.assertTrue(ui.should_ai_move_for_turn(ui.MODE_PVAI, "NORMAL", "BLACK", ui.HUMAN_COLOR_WHITE))
        self.assertFalse(ui.should_ai_move_for_turn(ui.MODE_PVAI, "NORMAL", "WHITE", ui.HUMAN_COLOR_WHITE))
        self.assertTrue(ui.should_ai_move_for_turn(ui.MODE_PVAI, "NORMAL", "WHITE", ui.HUMAN_COLOR_BLACK))
        self.assertFalse(ui.should_ai_move_for_turn(ui.MODE_PVP, "NORMAL", "BLACK", ui.HUMAN_COLOR_WHITE))

        self.assertEqual(ui.board_to_display_coords(0, 0, False), (0, 0))
        self.assertEqual(ui.board_to_display_coords(0, 0, True), (7, 7))
        self.assertEqual(ui.display_to_board_coords(7, 7, True), (0, 0))

        self.assertEqual(ui.format_clock_time(None), "∞")
        self.assertEqual(ui.format_clock_time(180), "03:00")
        self.assertEqual(ui.format_clock_time(5.4), "0:05.4")
        self.assertEqual(ui.format_clock_time(0), "0:00.0")

        self.assertTrue(ui.is_own_piece("P", True))
        self.assertFalse(ui.is_own_piece("p", True))
        self.assertTrue(ui.is_own_piece("p", False))
        self.assertFalse(ui.is_own_piece(".", False))

        self.assertAlmostEqual(ui.compute_advantage_ratio(0), 0.5)
        self.assertGreater(ui.compute_advantage_ratio(4), 0.5)
        self.assertLess(ui.compute_advantage_ratio(-4), 0.5)

    def test_get_board_geometry(self):
        board_size, square_size, offset_x, offset_y = ui.get_board_geometry(800, 600)
        self.assertAlmostEqual(board_size / 8, square_size)
        self.assertGreaterEqual(offset_x, 0)
        self.assertGreaterEqual(offset_y, 44)


class GambitUIFlowTests(unittest.TestCase):
    def test_pvai_replay_back_forward_resign_and_no_undo(self):
        prev_cwd = os.getcwd()
        os.chdir(ROOT_DIR)
        root = tk.Tk()
        root.withdraw()
        app = ui.GambitUI(root, game_mode=ui.MODE_PVAI, prompt_mode_on_start=False)
        results = {}

        def step_wait_init():
            if app.engine_busy:
                root.after(40, step_wait_init)
                return
            results["has_undo_button"] = hasattr(app, "undo_button")
            results["has_undo_method"] = hasattr(app, "undo_last_turn")
            results["init_moves"] = len(app.legal_moves)
            results["default_depth"] = app.get_ai_depth()
            results["default_time_limit"] = app.get_ai_time_limit()
            results["init_eval_headline"] = app.eval_headline_label.cget("text")
            app.difficulty_var.set("Easy (Depth 1)")
            results["easy_depth"] = app.get_ai_depth()
            app.make_move("e2e4")
            root.after(40, step_wait_ai)

        def step_wait_ai():
            if app.engine_busy or len(app.move_history) < 2:
                root.after(40, step_wait_ai)
                return
            results["after_ai_history"] = list(app.move_history)
            results["ai_eval_text"] = app.ai_eval_label.cget("text")
            results["live_view_index"] = app.view_index
            # Animated step back twice to move 0
            app.step_back(animate=True)
            root.after(40, step_wait_back1)

        def step_wait_back1():
            if app.animating:
                root.after(30, step_wait_back1)
                return
            results["back1_view_index"] = app.view_index
            results["back1_is_live"] = app.is_viewing_live()
            # Cannot play move while reviewing history
            app.make_move("d2d4")
            results["blocked_move_history_len"] = len(app.move_history)
            app.step_back(animate=True)
            root.after(40, step_wait_back2)

        def step_wait_back2():
            if app.animating:
                root.after(30, step_wait_back2)
                return
            results["back2_view_index"] = app.view_index
            results["back2_e2_piece"] = app.board[6][4]
            app.step_forward(animate=True)
            root.after(40, step_wait_fwd1)

        def step_wait_fwd1():
            if app.animating:
                root.after(30, step_wait_fwd1)
                return
            results["fwd1_view_index"] = app.view_index
            app.jump_to_live()
            results["jumped_live"] = app.is_viewing_live()
            results["jumped_view_index"] = app.view_index
            # Resign in PvAI (White resigns)
            app.resign_game(confirm=False)
            results["pvai_resign_status"] = app.game_status
            results["pvai_resign_btn_after"] = str(app.resign_button["state"])
            app.make_move("d2d4")
            results["post_resign_history_len"] = len(app.move_history)
            app.new_game(mode=ui.MODE_PVAI)
            root.after(40, step_wait_new_game)

        def step_wait_new_game():
            if app.engine_busy:
                root.after(40, step_wait_new_game)
                return
            results["reset_status"] = app.game_status
            results["reset_history_len"] = len(app.move_history)
            results["done"] = True
            app.close()

        try:
            root.after(100, step_wait_init)
            root.mainloop()
        finally:
            os.chdir(prev_cwd)
            if app.engine.poll() is None:
                app.engine.terminate()
                app.engine.wait(timeout=2)
            if app.engine.stdin:
                app.engine.stdin.close()
            if app.engine.stdout:
                app.engine.stdout.close()

        self.assertTrue(results.get("done"))
        self.assertFalse(results["has_undo_button"])
        self.assertFalse(results["has_undo_method"])
        self.assertEqual(results["init_moves"], 20)
        self.assertEqual(results["init_eval_headline"], "Position is equal: 0.0")
        self.assertEqual(results["default_depth"], 3)
        self.assertEqual(results["default_time_limit"], 2.0)
        self.assertEqual(results["easy_depth"], 1)
        self.assertEqual(len(results["after_ai_history"]), 2)
        self.assertEqual(results["after_ai_history"][0], "e2e4")
        self.assertIn("AI Positional Eval", results["ai_eval_text"])
        self.assertEqual(results["live_view_index"], 2)
        self.assertEqual(results["back1_view_index"], 1)
        self.assertFalse(results["back1_is_live"])
        self.assertEqual(results["blocked_move_history_len"], 2)
        self.assertEqual(results["back2_view_index"], 0)
        self.assertEqual(results["back2_e2_piece"], "P")
        self.assertEqual(results["fwd1_view_index"], 1)
        self.assertTrue(results["jumped_live"])
        self.assertEqual(results["jumped_view_index"], 2)
        self.assertEqual(results["pvai_resign_status"], "RESIGNED_WHITE")
        self.assertEqual(results["pvai_resign_btn_after"], "disabled")
        self.assertEqual(results["post_resign_history_len"], 2)
        self.assertEqual(results["reset_status"], "NORMAL")
        self.assertEqual(results["reset_history_len"], 0)

    def test_pvp_mode_replay_eval_and_resign_both_sides(self):
        prev_cwd = os.getcwd()
        os.chdir(ROOT_DIR)
        root = tk.Tk()
        root.withdraw()
        app = ui.GambitUI(root, game_mode=ui.MODE_PVP, prompt_mode_on_start=False)
        results = {}

        def step_init():
            if app.engine_busy:
                root.after(40, step_init)
                return
            results["pvp_mode_label"] = app.mode_label.cget("text")
            results["pvp_diff_state"] = str(app.difficulty_menu["state"])
            app.select_mode_from_sidebar(ui.MODE_PVAI)
            results["sidebar_switched_to_pvai"] = app.game_mode
            app.select_mode_from_sidebar(ui.MODE_PVP)
            results["sidebar_switched_back_to_pvp"] = app.game_mode
            app.make_move("e2e4")
            root.after(40, step_after_white)

        def step_after_white():
            if app.engine_busy:
                root.after(40, step_after_white)
                return
            results["after_white_history"] = list(app.move_history)
            results["after_white_turn"] = app.white_turn
            app.make_move("d7d5")
            root.after(40, step_after_black)

        def step_after_black():
            if app.engine_busy:
                root.after(40, step_after_black)
                return
            results["after_black_history"] = list(app.move_history)
            results["after_black_turn"] = app.white_turn
            app.make_move("e4d5")
            root.after(40, step_after_capture)

        def step_after_capture():
            if app.engine_busy:
                root.after(40, step_after_capture)
                return
            results["capture_headline"] = app.eval_headline_label.cget("text")
            results["capture_cpp_eval"] = app.engine_eval_label.cget("text")
            results["capture_diff"] = app.material_diff_label.cget("text")
            # Step back 1 move -> evaluation updates to 0.0 without altering move_history
            app.step_back(animate=False)
            results["review_headline"] = app.eval_headline_label.cget("text")
            results["review_history_intact"] = list(app.move_history)
            app.jump_to_live()
            results["live_headline_restored"] = app.eval_headline_label.cget("text")
            # Black's turn in PvP -> Black resigns
            app.resign_game(confirm=False)
            results["pvp_black_resign_status"] = app.game_status
            app.new_game(mode=ui.MODE_PVAI)
            root.after(40, step_after_switch)

        def step_after_switch():
            if app.engine_busy:
                root.after(40, step_after_switch)
                return
            results["switched_mode"] = app.game_mode
            results["switched_label"] = app.mode_label.cget("text")
            results["switched_history"] = list(app.move_history)
            results["switched_diff_state"] = str(app.difficulty_menu["state"])
            app.difficulty_var.set("Easy (Depth 1)")
            app.make_move("e2e4")
            root.after(40, step_after_pvai_move)

        def step_after_pvai_move():
            if app.engine_busy or len(app.move_history) < 2:
                root.after(40, step_after_pvai_move)
                return
            results["pvai_history"] = list(app.move_history)
            results["done"] = True
            app.close()

        try:
            root.after(100, step_init)
            root.mainloop()
        finally:
            os.chdir(prev_cwd)
            if app.engine.poll() is None:
                app.engine.terminate()
                app.engine.wait(timeout=2)
            if app.engine.stdin:
                app.engine.stdin.close()
            if app.engine.stdout:
                app.engine.stdout.close()

        self.assertTrue(results.get("done"))
        self.assertIn("Player vs Player", results["pvp_mode_label"])
        self.assertEqual(results["pvp_diff_state"], "disabled")
        self.assertEqual(results["sidebar_switched_to_pvai"], ui.MODE_PVAI)
        self.assertEqual(results["sidebar_switched_back_to_pvp"], ui.MODE_PVP)
        self.assertEqual(results["after_white_history"], ["e2e4"])
        self.assertFalse(results["after_white_turn"])
        self.assertEqual(results["after_black_history"], ["e2e4", "d7d5"])
        self.assertTrue(results["after_black_turn"])
        self.assertEqual(results["capture_headline"], "White is better: +1.0")
        self.assertIn("+1.0", results["capture_cpp_eval"])
        self.assertIn("pawn", results["capture_diff"])
        self.assertEqual(results["review_headline"], "Position is equal: 0.0")
        self.assertEqual(results["review_history_intact"], ["e2e4", "d7d5", "e4d5"])
        self.assertEqual(results["live_headline_restored"], "White is better: +1.0")
        self.assertEqual(results["pvp_black_resign_status"], "RESIGNED_BLACK")
        self.assertEqual(results["switched_mode"], ui.MODE_PVAI)
        self.assertIn("Player vs AI", results["switched_label"])
        self.assertEqual(results["switched_history"], [])
        self.assertEqual(results["switched_diff_state"], "normal")
        self.assertEqual(len(results["pvai_history"]), 2)
        self.assertEqual(results["pvai_history"][0], "e2e4")

    def test_play_as_black_flip_board_and_clock_timeout(self):
        prev_cwd = os.getcwd()
        os.chdir(ROOT_DIR)
        root = tk.Tk()
        root.withdraw()
        app = ui.GambitUI(
            root,
            game_mode=ui.MODE_PVAI,
            prompt_mode_on_start=False,
            human_color=ui.HUMAN_COLOR_BLACK,
            time_control="Blitz (3+2)"
        )
        app.difficulty_var.set("Easy (Depth 1)")
        results = {}

        def step_wait_ai_opening():
            if app.engine_busy or len(app.move_history) < 1:
                root.after(40, step_wait_ai_opening)
                return
            results["ai_opened_history"] = list(app.move_history)
            results["auto_flipped"] = app.board_flipped
            results["turn_after_ai_open"] = app.white_turn
            results["white_time_after_open"] = app.white_time
            results["top_clock_before_flip"] = app.top_clock_name.cget("text")
            app.flip_board()
            results["flipped_off"] = app.board_flipped
            results["top_clock_after_flip"] = app.top_clock_name.cget("text")
            app.flip_board()
            app.make_move("e7e5")
            root.after(40, step_wait_ai_reply)

        def step_wait_ai_reply():
            if app.engine_busy or len(app.move_history) < 3:
                root.after(40, step_wait_ai_reply)
                return
            results["after_black_move_history"] = list(app.move_history)
            results["turn_after_ai_reply"] = app.white_turn
            # Trigger timeout for Black
            app._handle_timeout(False)
            results["timeout_status"] = app.game_status
            results["resign_btn_after_timeout"] = str(app.resign_button["state"])
            app.make_move("d7d5")
            results["history_len_after_timeout_move"] = len(app.move_history)
            app.new_game(mode=ui.MODE_PVP, time_control="Untimed")
            root.after(40, step_wait_reset)

        def step_wait_reset():
            if app.engine_busy:
                root.after(40, step_wait_reset)
                return
            results["reset_mode"] = app.game_mode
            results["reset_flipped"] = app.board_flipped
            results["reset_clock_text"] = app.top_clock_time.cget("text")
            results["reset_status"] = app.game_status
            results["done"] = True
            app.close()

        try:
            root.after(100, step_wait_ai_opening)
            root.mainloop()
        finally:
            os.chdir(prev_cwd)
            if app.engine.poll() is None:
                app.engine.terminate()
                app.engine.wait(timeout=2)
            if app.engine.stdin:
                app.engine.stdin.close()
            if app.engine.stdout:
                app.engine.stdout.close()

        self.assertTrue(results.get("done"))
        self.assertEqual(len(results["ai_opened_history"]), 1)
        self.assertTrue(results["auto_flipped"])
        self.assertFalse(results["turn_after_ai_open"])
        self.assertGreater(results["white_time_after_open"], 180.0)
        self.assertIn("White", results["top_clock_before_flip"])
        self.assertFalse(results["flipped_off"])
        self.assertIn("Black", results["top_clock_after_flip"])
        self.assertEqual(len(results["after_black_move_history"]), 3)
        self.assertEqual(results["after_black_move_history"][1], "e7e5")
        self.assertFalse(results["turn_after_ai_reply"])
        self.assertEqual(results["timeout_status"], "TIMEOUT_BLACK")
        self.assertEqual(results["resign_btn_after_timeout"], "disabled")
        self.assertEqual(results["history_len_after_timeout_move"], 3)
        self.assertEqual(results["reset_mode"], ui.MODE_PVP)
        self.assertFalse(results["reset_flipped"])
        self.assertEqual(results["reset_clock_text"], "∞")
        self.assertEqual(results["reset_status"], "NORMAL")

    def test_sidebar_time_and_side_selectors(self):
        prev_cwd = os.getcwd()
        os.chdir(ROOT_DIR)
        root = tk.Tk()
        root.withdraw()
        app = ui.GambitUI(root, game_mode=ui.MODE_PVAI, prompt_mode_on_start=False)
        app.difficulty_var.set("Easy (Depth 1)")
        results = {}

        def step_init():
            if app.engine_busy:
                root.after(40, step_init)
                return
            app.on_sidebar_time_change("Blitz (3+2)")
            results["blitz_white_time"] = app.white_time
            results["blitz_clock_text"] = app.bottom_clock_time.cget("text")
            app.on_sidebar_side_change("Black")
            root.after(40, step_wait_ai_open)

        def step_wait_ai_open():
            if app.engine_busy or len(app.move_history) < 1:
                root.after(40, step_wait_ai_open)
                return
            results["side_black_flipped"] = app.board_flipped
            results["side_black_ai_opened"] = len(app.move_history)
            app.close()

        try:
            root.after(100, step_init)
            root.mainloop()
        finally:
            os.chdir(prev_cwd)
            if app.engine.poll() is None:
                app.engine.terminate()
                app.engine.wait(timeout=2)
            if app.engine.stdin:
                app.engine.stdin.close()
            if app.engine.stdout:
                app.engine.stdout.close()

        self.assertEqual(results["blitz_white_time"], 180.0)
        self.assertEqual(results["blitz_clock_text"], "03:00")
        self.assertTrue(results["side_black_flipped"])
        self.assertEqual(results["side_black_ai_opened"], 1)


if __name__ == "__main__":
    unittest.main()
