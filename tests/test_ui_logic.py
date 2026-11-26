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
        text, _ = ui.format_status_text("NORMAL", False, True)
        self.assertIn("AI thinking", text)

        text, _ = ui.format_status_text("CHECK", True, False)
        self.assertEqual(text, "White to move — CHECK")

        text, _ = ui.format_status_text("CHECKMATE", True, False)
        self.assertEqual(text, "CHECKMATE — Black wins")

        text, _ = ui.format_status_text("STALEMATE", False, False)
        self.assertEqual(text, "STALEMATE — Draw")

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
        app = ui.GambitUI(root)
        results = {}

        def step_wait_init():
            if app.engine_busy:
                root.after(40, step_wait_init)
                return
            results["init_moves"] = len(app.legal_moves)
            app.make_move("e2e4")
            root.after(40, step_wait_ai)

        def step_wait_ai():
            if app.engine_busy or len(app.move_history) < 2:
                root.after(40, step_wait_ai)
                return
            results["after_ai_history"] = list(app.move_history)
            results["undo_state_before"] = str(app.undo_button["state"])
            app.undo_last_turn()
            root.after(40, step_wait_undo)

        def step_wait_undo():
            if app.engine_busy:
                root.after(40, step_wait_undo)
                return
            results["after_undo_history"] = list(app.move_history)
            results["after_undo_moves"] = len(app.legal_moves)
            results["after_undo_turn"] = app.white_turn
            app.new_game()
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
        self.assertEqual(len(results["after_ai_history"]), 2)
        self.assertEqual(results["after_ai_history"][0], "e2e4")
        self.assertEqual(results["undo_state_before"], "normal")
        self.assertEqual(results["after_undo_history"], [])
        self.assertEqual(results["after_undo_moves"], 20)
        self.assertTrue(results["after_undo_turn"])


if __name__ == "__main__":
    unittest.main()
