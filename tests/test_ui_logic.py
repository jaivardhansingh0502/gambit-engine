import os
import sys
import tempfile
import tkinter as tk
import unittest
from unittest import mock

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
            app.difficulty_var.set("Easy (Depth 2)")
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
        self.assertEqual(results["default_depth"], 4)
        self.assertEqual(results["default_time_limit"], 1.5)
        self.assertEqual(results["easy_depth"], 2)
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
            results["capture_ai_eval"] = app.ai_eval_label.cget("text")
            results["capture_cpp_eval"] = app.engine_eval_label.cget("text")
            results["capture_diff"] = app.material_diff_label.cget("text")
            # Step back to initial position -> real-time AI+ eval restores equal without altering move_history
            app.step_back(animate=False)
            app.step_back(animate=False)
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
        self.assertTrue(results["capture_headline"].startswith("White is better: +"))
        self.assertIn("Search AI+", results["capture_ai_eval"])
        self.assertIn("+1.0", results["capture_cpp_eval"])
        self.assertIn("pawn", results["capture_diff"])
        self.assertEqual(results["review_headline"], "Position is equal: 0.0")
        self.assertEqual(results["review_history_intact"], ["e2e4", "d7d5", "e4d5"])
        self.assertEqual(results["live_headline_restored"], results["capture_headline"])
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
        app.difficulty_var.set("Easy (Depth 2)")
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
        app.difficulty_var.set("Easy (Depth 2)")
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

    def test_startup_modal_and_live_clock_ticking(self):
        prev_cwd = os.getcwd()
        os.chdir(ROOT_DIR)
        root = tk.Tk()
        root.withdraw()
        app = ui.GambitUI(root, prompt_mode_on_start=True, settings_path=None)
        results = {}

        def step_interact_modal():
            for w in root.winfo_children():
                if isinstance(w, tk.Toplevel):
                    for child in w.winfo_children():
                        if isinstance(child, tk.Frame):
                            for sub in child.winfo_children():
                                if isinstance(sub, tk.Frame):
                                    for om in sub.winfo_children():
                                        if isinstance(om, tk.OptionMenu):
                                            var_name = om.cget("textvariable")
                                            if root.getvar(var_name) == "Untimed":
                                                root.setvar(var_name, "Blitz (3+2)")
                            for btn in child.winfo_children():
                                if isinstance(btn, tk.Button) and "Player vs AI" in btn.cget("text"):
                                    btn.invoke()
                                    root.after(700, step_check_clock)
                                    return
            root.after(40, step_interact_modal)

        def step_check_clock():
            results["in_modal"] = app._in_modal
            results["time_control"] = app.time_control_name
            results["white_time_after"] = app.white_time
            results["done"] = True
            app.close()

        try:
            root.after(120, step_interact_modal)
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
        self.assertFalse(results["in_modal"])
        self.assertEqual(results["time_control"], "Blitz (3+2)")
        self.assertLess(results["white_time_after"], 179.6)

    def test_san_captures_draw_offer_fen_pgn_hint_and_drag_drop(self):
        prev_cwd = os.getcwd()
        os.chdir(ROOT_DIR)
        root = tk.Tk()
        root.deiconify()
        root.geometry("1280x680")
        app = ui.GambitUI(root, game_mode=ui.MODE_PVP, prompt_mode_on_start=False)
        results = {}

        class DummyEvent:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        def sq_center(sq):
            width = app.canvas.winfo_width()
            height = app.canvas.winfo_height()
            _, sq_size, ox, oy = ui.get_board_geometry(width, height)
            r, c = ui.notation_to_coords(sq)
            dr, dc = ui.board_to_display_coords(r, c, app.board_flipped)
            return ox + (dc + 0.5) * sq_size, oy + (dr + 0.5) * sq_size

        def step_init():
            if app.engine_busy:
                root.after(40, step_init)
                return
            root.update_idletasks()
            app.toggle_sound()
            results["sound_toggled_on"] = app.sound_enabled
            app.toggle_sound()
            results["sound_toggled_off"] = app.sound_enabled
            # Drag e2 to e4
            x1, y1 = sq_center("e2")
            x2, y2 = sq_center("e4")
            app.on_mouse_down(DummyEvent(x1, y1))
            app.on_mouse_drag(DummyEvent((x1 + x2) / 2, (y1 + y2) / 2))
            app.on_mouse_up(DummyEvent(x2, y2))
            root.after(40, step_after_drag)

        def step_after_drag():
            if app.engine_busy:
                root.after(40, step_after_drag)
                return
            results["after_drag_move"] = list(app.move_history)
            results["after_drag_san"] = list(app.san_history)
            app.make_move("d7d5")
            root.after(40, step_after_d5)

        def step_after_d5():
            if app.engine_busy:
                root.after(40, step_after_d5)
                return
            app.make_move("e4d5")
            root.after(40, step_after_capture)

        def step_after_capture():
            if app.engine_busy:
                root.after(40, step_after_capture)
                return
            results["san_after_capture"] = list(app.san_history)
            results["captured_by_white"] = list(app.captured_by_white)
            results["bottom_tray_live"] = app.bottom_captured_label.cget("text")
            # Check replay restores captured tray to empty at index 0
            app._apply_view_index(0)
            results["bottom_tray_at_0"] = app.bottom_captured_label.cget("text")
            app.jump_to_live()
            results["bottom_tray_re_live"] = app.bottom_captured_label.cget("text")
            # Test hint arrow on live board
            app.request_hint()
            root.after(40, step_after_hint)

        def step_after_hint():
            if app.engine_busy:
                root.after(40, step_after_hint)
                return
            results["hint_move"] = app.hint_move
            # Export PGN while active
            results["pgn_before_draw"] = app.export_pgn(save_dialog=False)
            # Test draw offer
            app.offer_draw(confirm=False)
            results["status_after_draw"] = app.game_status
            results["draw_btn_after"] = str(app.draw_button["state"])
            # Test loading custom Scholar's Mate FEN
            app.load_fen("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4")
            root.after(40, step_after_fen)

        def step_after_fen():
            if app.engine_busy:
                root.after(40, step_after_fen)
                return
            results["fen_loaded_status"] = app.game_status
            results["fen_loaded_h5"] = app.board[3][7]
            results["fen_initial_stored"] = app.initial_fen
            # Request hint in Scholar's mate -> should suggest h5f7
            app.request_hint()
            root.after(40, step_after_mate_hint)

        def step_after_mate_hint():
            if app.engine_busy:
                root.after(40, step_after_mate_hint)
                return
            results["mate_hint_move"] = app.hint_move
            results["done"] = True
            app.close()

        try:
            root.after(120, step_init)
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
        self.assertTrue(results["sound_toggled_on"])
        self.assertFalse(results["sound_toggled_off"])
        self.assertEqual(results["after_drag_move"], ["e2e4"])
        self.assertEqual(results["after_drag_san"], ["e4"])
        self.assertEqual(results["san_after_capture"], ["e4", "d5", "exd5"])
        self.assertEqual(results["captured_by_white"], ["p"])
        self.assertIn("♟", results["bottom_tray_live"])
        self.assertEqual(results["bottom_tray_at_0"], "—")
        self.assertIn("♟", results["bottom_tray_re_live"])
        self.assertIsNotNone(results["hint_move"])
        self.assertIn("1. e4 d5 2. exd5 *", results["pgn_before_draw"])
        self.assertEqual(results["status_after_draw"], "DRAW_AGREED")
        self.assertEqual(results["draw_btn_after"], "disabled")
        self.assertEqual(results["fen_loaded_status"], "NORMAL")
        self.assertEqual(results["fen_loaded_h5"], "Q")
        self.assertIn("4 4", results["fen_initial_stored"])
        self.assertEqual(results["mate_hint_move"], "h5f7")

    def test_option_b_themes_history_click_annotations_eval_graph_and_premove(self):
        prev_cwd = os.getcwd()
        os.chdir(ROOT_DIR)
        root = tk.Tk()
        root.deiconify()
        root.geometry("1280x680")
        app = ui.GambitUI(root, game_mode=ui.MODE_PVP, prompt_mode_on_start=False)
        results = {}

        class DummyEvent:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        def sq_center(sq):
            width = app.canvas.winfo_width()
            height = app.canvas.winfo_height()
            _, sq_size, ox, oy = ui.get_board_geometry(width, height)
            r, c = ui.notation_to_coords(sq)
            dr, dc = ui.board_to_display_coords(r, c, app.board_flipped)
            return ox + (dc + 0.5) * sq_size, oy + (dr + 0.5) * sq_size

        def step_init():
            if app.engine_busy:
                root.after(40, step_init)
                return
            root.update_idletasks()
            app.set_board_theme("Walnut Wood")
            results["theme_name"] = app.board_theme_name

            # Right-click highlight + arrow
            ex, ey = sq_center("e4")
            dx, dy = sq_center("d5")
            app.on_right_down(DummyEvent(ex, ey))
            app.on_right_up(DummyEvent(ex, ey))
            results["highlight_added"] = "e4" in app.highlighted_squares
            app.on_right_down(DummyEvent(ex, ey))
            app.on_right_up(DummyEvent(dx, dy))
            results["arrow_added"] = ("e4", "d5") in app.user_arrows

            # Play 2 moves and test clickable Move History + Eval Graph
            app.make_move("e2e4", animate=False)
            root.after(40, step_after_w1)

        def step_after_w1():
            if app.engine_busy:
                root.after(40, step_after_w1)
                return
            app.make_move("e7e5", animate=False)
            root.after(40, step_after_b1)

        def step_after_b1():
            if app.engine_busy:
                root.after(40, step_after_b1)
                return
            results["annotations_cleared_on_move"] = (
                len(app.highlighted_squares) == 0 and len(app.user_arrows) == 0
            )
            results["eval_hist_len"] = len(app.eval_history)
            bbox = app.history_list.bbox(0)
            lw = app.history_list.winfo_width()
            app.on_history_click(DummyEvent(lw * 0.25, bbox[1] + 2))
            results["clicked_white_ply"] = app.view_index
            app.on_history_click(DummyEvent(lw * 0.75, bbox[1] + 2))
            results["clicked_black_ply"] = app.view_index

            # Eval graph click back to start
            app.on_eval_graph_click(DummyEvent(1, 5))
            results["eval_graph_jumped_0"] = app.view_index
            app.jump_to_live()

            # Switch to PvAI and verify Premove queues during engine_busy and executes after
            app.new_game(mode=ui.MODE_PVAI)
            root.after(40, step_pvai_ready)

        def step_pvai_ready():
            if app.engine_busy:
                root.after(40, step_pvai_ready)
                return
            app.difficulty_var.set("Easy (Depth 2)")
            # Play 1. e4 and immediately queue premove d2d4 while AI is thinking
            app.make_move("e2e4", animate=False)
            d2x, d2y = sq_center("d2")
            d4x, d4y = sq_center("d4")
            app.on_mouse_down(DummyEvent(d2x, d2y))
            app.on_mouse_down(DummyEvent(d4x, d4y))
            results["premove_queued"] = app.premove
            root.after(150, step_wait_premove_exec)

        def step_wait_premove_exec():
            if app.engine_busy or len(app.move_history) < 4:
                root.after(50, step_wait_premove_exec)
                return
            results["history_after_premove"] = list(app.move_history)
            results["premove_cleared"] = app.premove is None
            results["done"] = True
            app.close()

        try:
            root.after(120, step_init)
            root.after(12000, lambda: app.close() if not results.get("done") else None)
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
        self.assertEqual(results["theme_name"], "Walnut Wood")
        self.assertTrue(results["highlight_added"])
        self.assertTrue(results["arrow_added"])
        self.assertTrue(results["annotations_cleared_on_move"])
        self.assertEqual(results["eval_hist_len"], 3)
        self.assertEqual(results["clicked_white_ply"], 1)
        self.assertEqual(results["clicked_black_ply"], 2)
        self.assertEqual(results["eval_graph_jumped_0"], 0)
        self.assertEqual(results["premove_queued"], "d2d4")
        self.assertGreaterEqual(len(results["history_after_premove"]), 4)
        self.assertEqual(results["history_after_premove"][2], "d2d4")
        self.assertTrue(results["premove_cleared"])

    def test_option_d_opening_banner_and_post_game_review(self):
        prev_cwd = os.getcwd()
        os.chdir(ROOT_DIR)
        root = tk.Tk()
        root.withdraw()
        app = ui.GambitUI(root, game_mode=ui.MODE_PVP, prompt_mode_on_start=False)
        results = {}
        moves_to_play = ["f2f3", "e7e5", "g2g4", "d8h4"]
        move_step = {"idx": 0}

        def step_init():
            if app.engine_busy:
                root.after(40, step_init)
                return
            results["init_opening"] = app.opening_label.cget("text")
            step_play_next()

        def step_play_next():
            if app.engine_busy or app.animating:
                root.after(30, step_play_next)
                return
            if move_step["idx"] < len(moves_to_play):
                mv = moves_to_play[move_step["idx"]]
                move_step["idx"] += 1
                app.make_move(mv, animate=False)
                root.after(30, step_play_next)
                return
            step_wait_mate()

        def step_wait_mate():
            if app.engine_busy or len(app.move_history) < 4:
                root.after(40, step_wait_mate)
                return
            results["mate_status"] = app.game_status
            results["review_btn_ready"] = str(app.review_game_button["state"])
            app.review_game()
            root.after(60, step_wait_review)

        def step_wait_review():
            if app.review_busy or not app.review_annotations:
                root.after(50, step_wait_review)
                return
            results["annotations_len"] = len(app.review_annotations)
            results["g4_symbol"] = app.review_annotations[2]["symbol"]
            results["summary"] = dict(app.review_summary)
            results["banner_after_review"] = app.opening_label.cget("text")
            results["history_row1"] = app.history_list.get(0)
            results["history_row2"] = app.history_list.get(1)
            # Viewing blunder move 3 (g2g4) should populate best move recommendation
            app._apply_view_index(3)
            results["blunder_best_move"] = app.review_best_move
            results["done"] = True
            app.close()

        try:
            root.after(120, step_init)
            root.after(10000, lambda: app.close() if not results.get("done") else None)
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
        self.assertEqual(results["init_opening"], "Opening: Starting Position")
        self.assertEqual(results["mate_status"], "CHECKMATE")
        self.assertEqual(results["review_btn_ready"], "normal")
        self.assertEqual(results["annotations_len"], 4)
        self.assertEqual(results["g4_symbol"], "??")
        self.assertIn("%", results["banner_after_review"])
        self.assertIn("g4??", results["history_row2"])
        self.assertIsNotNone(results["blunder_best_move"])
        self.assertGreaterEqual(results["summary"]["blunders"], 1)

    def test_option_e_settings_persistence_custom_time_and_icon(self):
        prev_cwd = os.getcwd()
        os.chdir(ROOT_DIR)
        tmpdir = tempfile.TemporaryDirectory()
        settings_file = os.path.join(tmpdir.name, "gambit_prefs.json")

        def run_session_1():
            root = tk.Tk()
            root.withdraw()
            app = ui.GambitUI(
                root,
                game_mode=ui.MODE_PVAI,
                prompt_mode_on_start=False,
                settings_path=settings_file,
            )
            out = {}

            def step_init():
                if app.engine_busy:
                    root.after(40, step_init)
                    return
                app.set_board_theme("Slate Blue")
                app.difficulty_var.set("Hard (Depth 6)")
                app.on_sidebar_difficulty_change("Hard (Depth 6)")
                label = app.apply_custom_time_control(7, 5, confirm_reset=False)
                out["custom_label"] = label
                out["white_time"] = app.white_time
                out["icon_exists"] = os.path.exists(ui.DEFAULT_APP_ICON_PATH)
                app.close()

            try:
                root.after(100, step_init)
                root.mainloop()
            finally:
                if app.engine.poll() is None:
                    app.engine.terminate()
                    app.engine.wait(timeout=2)
                if app.engine.stdin:
                    app.engine.stdin.close()
                if app.engine.stdout:
                    app.engine.stdout.close()
            return out

        def run_session_2():
            root = tk.Tk()
            root.withdraw()
            app = ui.GambitUI(
                root,
                prompt_mode_on_start=False,
                settings_path=settings_file,
            )
            out = {}

            def step_verify():
                if app.engine_busy:
                    root.after(40, step_verify)
                    return
                out["loaded_theme"] = app.board_theme_name
                out["loaded_diff"] = app.difficulty_var.get()
                out["loaded_tc"] = app.time_control_name
                out["loaded_white_time"] = app.white_time
                app.close()

            try:
                root.after(100, step_verify)
                root.mainloop()
            finally:
                if app.engine.poll() is None:
                    app.engine.terminate()
                    app.engine.wait(timeout=2)
                if app.engine.stdin:
                    app.engine.stdin.close()
                if app.engine.stdout:
                    app.engine.stdout.close()
            return out

        try:
            r1 = run_session_1()
            r2 = run_session_2()
        finally:
            ui.TIME_CONTROLS.pop("Custom (7+5)", None)
            os.chdir(prev_cwd)
            tmpdir.cleanup()

        self.assertEqual(r1["custom_label"], "Custom (7+5)")
        self.assertEqual(r1["white_time"], 420.0)
        self.assertTrue(r1["icon_exists"])
        self.assertEqual(r2["loaded_theme"], "Slate Blue")
        self.assertEqual(r2["loaded_diff"], "Hard (Depth 6)")
        self.assertEqual(r2["loaded_tc"], "Custom (7+5)")
        self.assertEqual(r2["loaded_white_time"], 420.0)

    def test_option_c_pgn_file_dialog_shortcuts_promotion_and_sound_paths(self):
        prev_cwd = os.getcwd()
        os.chdir(ROOT_DIR)
        tmpdir = tempfile.TemporaryDirectory()
        pgn_out = os.path.join(tmpdir.name, "test_export.pgn")
        root = tk.Tk()
        root.withdraw()
        app = ui.GambitUI(root, game_mode=ui.MODE_PVP, prompt_mode_on_start=False)
        results = {}

        def step_init():
            if app.engine_busy:
                root.after(40, step_init)
                return
            # 1. Sound enabled with mocked winsound.Beep
            app.sound_enabled = True
            with mock.patch("chess_utils.winsound") as mock_ws:
                ui.play_sound("move", enabled=True)
                root.after(40, lambda: results.__setitem__("sound_called", mock_ws.Beep.called))

            # 2. PGN save dialog path
            with mock.patch.object(ui.filedialog, "asksaveasfilename", return_value=pgn_out), \
                 mock.patch.object(ui.messagebox, "showinfo"):
                app.export_pgn(save_dialog=True)
            results["pgn_file_exists"] = os.path.exists(pgn_out)

            # 3. Choose promotion dialog selection ('q')
            def click_promo():
                for w in root.winfo_children():
                    if isinstance(w, tk.Toplevel) and w.title() == "Pawn Promotion":
                        for frame in w.winfo_children():
                            if isinstance(frame, tk.Frame):
                                for btn in frame.winfo_children():
                                    if isinstance(btn, tk.Button) and "Queen" in btn.cget("text"):
                                        btn.invoke()
                                        return
                root.after(20, click_promo)

            root.after(30, click_promo)
            results["promo_choice"] = app.choose_promotion(["a7a8q", "a7a8r", "a7a8b", "a7a8n"])

            # 4. Non-animated step_back/forward & shortcuts helpers
            app.make_move("e2e4", animate=False)
            root.after(50, step_after_mv)

        def step_after_mv():
            if app.engine_busy:
                root.after(40, step_after_mv)
                return
            app.step_back(animate=False)
            results["back_no_anim_idx"] = app.view_index
            app.step_forward(animate=False)
            results["fwd_no_anim_idx"] = app.view_index
            results["shortcut_allowed"] = app._shortcut_allowed()
            app._clear_board_annotations()
            results["done"] = True
            app.close()

        try:
            root.after(100, step_init)
            root.mainloop()
        finally:
            os.chdir(prev_cwd)
            tmpdir.cleanup()
            if app.engine.poll() is None:
                app.engine.terminate()
                app.engine.wait(timeout=2)
            if app.engine.stdin:
                app.engine.stdin.close()
            if app.engine.stdout:
                app.engine.stdout.close()

        self.assertTrue(results.get("done"))
        self.assertTrue(results["pgn_file_exists"])
        self.assertEqual(results["promo_choice"], "a7a8q")
        self.assertEqual(results["back_no_anim_idx"], 0)
        self.assertEqual(results["fwd_no_anim_idx"], 1)
        self.assertTrue(results["shortcut_allowed"])

    def test_engine_auto_recovers_after_process_termination(self):
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
            app.make_move("e2e4", animate=False)
            root.after(50, step_kill_engine)

        def step_kill_engine():
            if app.engine_busy or len(app.move_history) < 1:
                root.after(40, step_kill_engine)
                return
            # Simulate engine process dying unexpectedly before next move
            app.engine.terminate()
            app.engine.wait(timeout=2)
            app.make_move("e7e5", animate=False)
            root.after(50, step_verify_recovery)

        def step_verify_recovery():
            if app.engine_busy or len(app.move_history) < 2:
                root.after(40, step_verify_recovery)
                return
            results["history"] = list(app.move_history)
            results["alive"] = app.engine.poll() is None
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
        self.assertEqual(results["history"], ["e2e4", "e7e5"])
        self.assertTrue(results["alive"])

    def test_realtime_ai_plus_evaluation_mate_and_replay(self):
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
            # Scholar's Mate threat (material is 0.0, but White has Mate in 1)
            app.load_fen("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4")
            root.after(50, step_after_fen)

        def step_after_fen():
            if app.engine_busy:
                root.after(40, step_after_fen)
                return
            results["mate1_headline"] = app.eval_headline_label.cget("text")
            results["mate1_ai_label"] = app.ai_eval_label.cget("text")
            results["mate1_cpp_label"] = app.engine_eval_label.cget("text")
            results["mate1_bar_score"] = app.current_eval_score
            app.make_move("h5f7", animate=False)
            root.after(50, step_after_mate)

        def step_after_mate():
            if app.engine_busy:
                root.after(40, step_after_mate)
                return
            results["checkmate_headline"] = app.eval_headline_label.cget("text")
            results["checkmate_ai_label"] = app.ai_eval_label.cget("text")
            results["eval_history_len"] = len(app.eval_history)
            app.step_back(animate=False)
            results["back_mate1_headline"] = app.eval_headline_label.cget("text")
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
        self.assertEqual(results["mate1_headline"], "White has Mate in M1")
        self.assertIn("+M1", results["mate1_ai_label"])
        self.assertIn("0.0", results["mate1_cpp_label"])
        self.assertEqual(results["mate1_bar_score"], 20.0)
        self.assertEqual(results["checkmate_headline"], "White wins (Mate)")
        self.assertIn("+M0", results["checkmate_ai_label"])
        self.assertEqual(results["eval_history_len"], 2)
        self.assertEqual(results["back_mate1_headline"], "White has Mate in M1")

    def test_option_a_and_d_pgn_import_play_here_library_themes_and_eval_bar(self):
        prev_cwd = os.getcwd()
        os.chdir(ROOT_DIR)
        tmpdir = tempfile.TemporaryDirectory()
        settings_file = os.path.join(tmpdir.name, "prefs.json")
        games_file = os.path.join(tmpdir.name, "saved_games.json")
        root = tk.Tk()
        root.geometry("1280x680")
        app = ui.GambitUI(
            root,
            game_mode=ui.MODE_PVP,
            prompt_mode_on_start=False,
            settings_path=settings_file,
            games_path=games_file,
        )
        results = {}

        def step_init():
            if app.engine_busy:
                root.after(40, step_init)
                return
            # 1. Option D: switch sidebar theme, toggle board eval bar off/on, verify preference persistence
            app.apply_sidebar_theme("Arctic Light")
            results["arctic_bg"] = app.history_frame.cget("bg")
            app.set_show_board_eval_bar(False)
            results["eval_bar_hidden"] = bool(app.board_eval_bar.winfo_ismapped())
            app.set_show_board_eval_bar(True)

            # 2. Option A: import a PGN game with Scholar's Mate, verify move history + opening + eval graph
            pgn = (
                '[Event "Scholar"]\n'
                '1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0'
            )
            app.load_pgn(pgn)
            root.after(60, step_after_pgn)

        def step_after_pgn():
            if app.engine_busy:
                root.after(40, step_after_pgn)
                return
            results["pgn_moves"] = list(app.move_history)
            results["pgn_san"] = list(app.san_history)
            results["pgn_status"] = app.game_status
            results["pgn_eval_len"] = len(app.eval_history)
            # Step back before Qxf7# and verify Play From Here turns live PvAI on at ply 6
            app.step_back(animate=False)
            results["play_here_state_at_back"] = str(app.play_from_here_button["state"])
            app.play_from_here(human_color=ui.HUMAN_COLOR_WHITE)
            root.after(60, step_after_play_here)

        def step_after_play_here():
            if app.engine_busy:
                root.after(40, step_after_play_here)
                return
            results["branch_len"] = len(app.move_history)
            results["branch_mode"] = app.game_mode
            results["branch_status"] = app.game_status
            # Play h5f7 checkmate -> triggers auto-save into saved_games.json!
            app.make_move("h5f7", animate=False)
            root.after(60, step_after_checkmate)

        def step_after_checkmate():
            if app.engine_busy:
                root.after(40, step_after_checkmate)
                return
            results["final_status"] = app.game_status
            saved = ui.load_saved_games(games_file)
            results["saved_count"] = len(saved)
            results["saved_outcome"] = saved[0]["outcome"] if saved else None
            # Verify material advantage badge when playing capture
            app.load_fen("rnbqkbn1/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            root.after(60, step_after_adv_fen)

        def step_after_adv_fen():
            if app.engine_busy:
                root.after(40, step_after_adv_fen)
                return
            results["bottom_adv_badge"] = app.bottom_advantage_label.cget("text")
            results["done"] = True
            app.close()

        try:
            root.after(100, step_init)
            root.mainloop()
        finally:
            os.chdir(prev_cwd)
            tmpdir.cleanup()
            if app.engine.poll() is None:
                app.engine.terminate()
                app.engine.wait(timeout=2)
            if app.engine.stdin:
                app.engine.stdin.close()
            if app.engine.stdout:
                app.engine.stdout.close()

        self.assertTrue(results.get("done"))
        self.assertEqual(results["arctic_bg"], ui.SIDEBAR_THEMES["Arctic Light"]["sidebar"])
        self.assertFalse(results["eval_bar_hidden"])
        self.assertEqual(
            results["pgn_moves"],
            ["e2e4", "e7e5", "d1h5", "b8c6", "f1c4", "g8f6", "h5f7"],
        )
        self.assertEqual(results["pgn_san"][-1], "Qxf7#")
        self.assertEqual(results["pgn_status"], "CHECKMATE")
        self.assertEqual(results["pgn_eval_len"], 8)
        self.assertEqual(results["play_here_state_at_back"], "normal")
        self.assertEqual(results["branch_len"], 6)
        self.assertEqual(results["branch_mode"], ui.MODE_PVAI)
        self.assertEqual(results["branch_status"], "NORMAL")
        self.assertEqual(results["final_status"], "CHECKMATE")
        self.assertEqual(results["saved_count"], 1)
        self.assertEqual(results["saved_outcome"], "WIN")
        self.assertEqual(results["bottom_adv_badge"], "+5")


if __name__ == "__main__":
    unittest.main()
