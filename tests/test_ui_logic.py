import os
import sys
import tkinter as tk
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import ui


class GambitUIHelperTests(unittest.TestCase):
    def test_square_to_notation(self):
        self.assertEqual(ui.square_to_notation(0, 0), "a8")
        self.assertEqual(ui.square_to_notation(7, 4), "e1")
        self.assertEqual(ui.square_to_notation(3, 7), "h5")

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

    def test_mode_and_advantage_helpers(self):
        self.assertTrue(ui.can_human_interact(ui.MODE_PVP, True))
        self.assertTrue(ui.can_human_interact(ui.MODE_PVP, False))
        self.assertTrue(ui.can_human_interact(ui.MODE_PVAI, True))
        self.assertFalse(ui.can_human_interact(ui.MODE_PVAI, False))

        self.assertTrue(ui.is_own_piece("P", True))
        self.assertFalse(ui.is_own_piece("p", True))
        self.assertTrue(ui.is_own_piece("p", False))
        self.assertFalse(ui.is_own_piece(".", False))

        self.assertEqual(ui.get_undo_count(ui.MODE_PVP, 2), 1)
        self.assertEqual(ui.get_undo_count(ui.MODE_PVAI, 2), 2)
        self.assertEqual(ui.get_undo_count(ui.MODE_PVAI, 1), 1)

        self.assertAlmostEqual(ui.compute_advantage_ratio(0), 0.5)
        self.assertGreater(ui.compute_advantage_ratio(4), 0.5)
        self.assertLess(ui.compute_advantage_ratio(-4), 0.5)

    def test_get_board_geometry(self):
        board_size, square_size, offset_x, offset_y = ui.get_board_geometry(800, 600)
        self.assertAlmostEqual(board_size / 8, square_size)
        self.assertGreaterEqual(offset_x, 0)
        self.assertGreaterEqual(offset_y, 44)


class GambitUIUndoFlowTests(unittest.TestCase):
    def test_move_undo_and_new_game_flow(self):
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
            results["init_moves"] = len(app.legal_moves)
            results["default_depth"] = app.get_ai_depth()
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
            results["undo_state_before"] = str(app.undo_button["state"])
            results["ai_eval_text"] = app.ai_eval_label.cget("text")
            app.undo_last_turn()
            root.after(40, step_wait_undo)

        def step_wait_undo():
            if app.engine_busy:
                root.after(40, step_wait_undo)
                return
            results["after_undo_history"] = list(app.move_history)
            results["after_undo_moves"] = len(app.legal_moves)
            results["after_undo_turn"] = app.white_turn
            app.new_game(mode=ui.MODE_PVAI)
            root.after(40, step_wait_new_game)

        def step_wait_new_game():
            if app.engine_busy:
                root.after(40, step_wait_new_game)
                return
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
        self.assertEqual(results["init_moves"], 20)
        self.assertEqual(results["init_eval_headline"], "Position is equal: 0.0")
        self.assertEqual(results["default_depth"], 2)
        self.assertEqual(results["easy_depth"], 1)
        self.assertEqual(len(results["after_ai_history"]), 2)
        self.assertEqual(results["after_ai_history"][0], "e2e4")
        self.assertEqual(results["undo_state_before"], "normal")
        self.assertIn("AI Search Eval", results["ai_eval_text"])
        self.assertEqual(results["after_undo_history"], [])
        self.assertEqual(results["after_undo_moves"], 20)
        self.assertTrue(results["after_undo_turn"])

    def test_pvp_mode_no_ai_capture_eval_and_mode_switch(self):
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
            app.undo_last_turn()
            root.after(40, step_after_pvp_undo)

        def step_after_pvp_undo():
            if app.engine_busy:
                root.after(40, step_after_pvp_undo)
                return
            results["undo_pvp_history"] = list(app.move_history)
            results["undo_pvp_headline"] = app.eval_headline_label.cget("text")
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
        self.assertEqual(results["after_white_history"], ["e2e4"])
        self.assertFalse(results["after_white_turn"])
        self.assertEqual(results["after_black_history"], ["e2e4", "d7d5"])
        self.assertTrue(results["after_black_turn"])
        self.assertEqual(results["capture_headline"], "White is better: +1.0")
        self.assertIn("+1.0", results["capture_cpp_eval"])
        self.assertIn("pawn", results["capture_diff"])
        self.assertEqual(results["undo_pvp_history"], ["e2e4", "d7d5"])
        self.assertEqual(results["undo_pvp_headline"], "Position is equal: 0.0")
        self.assertEqual(results["switched_mode"], ui.MODE_PVAI)
        self.assertIn("Player vs AI", results["switched_label"])
        self.assertEqual(results["switched_history"], [])
        self.assertEqual(results["switched_diff_state"], "normal")
        self.assertEqual(len(results["pvai_history"]), 2)
        self.assertEqual(results["pvai_history"][0], "e2e4")


if __name__ == "__main__":
    unittest.main()
