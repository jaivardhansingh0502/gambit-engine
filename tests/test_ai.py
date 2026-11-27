import os
import subprocess
import sys
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ai import AI, get_position, make_move, send_move_to_engine


class GambitAITests(unittest.TestCase):
    def setUp(self):
        self.engine = subprocess.Popen(
            [os.path.join(ROOT_DIR, "gambit.exe")],
            cwd=ROOT_DIR,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self.ai = AI(self.engine, verbose=False)

    def tearDown(self):
        if self.engine.poll() is None:
            self.engine.terminate()
            self.engine.wait(timeout=3)
        if self.engine.stdin:
            self.engine.stdin.close()
        if self.engine.stdout:
            self.engine.stdout.close()

    def play_moves(self, moves):
        for move in moves:
            resp = send_move_to_engine(self.engine, move)
            self.assertEqual(resp, "MOVE_OK", f"Expected MOVE_OK for {move}, got {resp}")
        return get_position(self.engine)

    def test_depth_parameter_and_state_preservation(self):
        board_before, moves_before, status_before, turn_before = self.play_moves(["e2e4"])

        best_d1 = self.ai.find_best_move(board_before, moves_before, turn_before, depth=1)
        nodes_d1 = self.ai.nodes_searched
        self.assertIn(best_d1, moves_before)

        board_mid, moves_mid, status_mid, turn_mid = get_position(self.engine)
        self.assertEqual(board_mid, board_before)
        self.assertEqual(moves_mid, moves_before)
        self.assertEqual(status_mid, status_before)
        self.assertEqual(turn_mid, turn_before)

        best_d2 = self.ai.find_best_move(board_before, moves_before, turn_before, depth=2)
        nodes_d2 = self.ai.nodes_searched
        self.assertIn(best_d2, moves_before)
        self.assertGreater(nodes_d2, nodes_d1)

    def test_finds_scholars_mate_in_one_for_white(self):
        board, moves, _, turn = self.play_moves([
            "e2e4", "e7e5",
            "f1c4", "b8c6",
            "d1h5", "g8f6",
        ])
        best = self.ai.find_best_move(board, moves, turn, depth=1)
        self.assertEqual(best, "h5f7")

    def test_finds_fools_mate_in_one_for_black(self):
        board, moves, _, turn = self.play_moves([
            "f2f3", "e7e5",
            "g2g4",
        ])
        best = self.ai.find_best_move(board, moves, turn, depth=1)
        self.assertEqual(best, "d8h4")

    def test_alpha_beta_prunes_nodes_vs_minimax(self):
        board, moves, _, turn = self.play_moves(["e2e4"])
        results = self.ai.compare_searches(board, moves, turn, depth=1)
        self.assertIn(results["Alpha-Beta"]["best_move"], moves)
        self.assertLessEqual(
            results["Alpha-Beta"]["nodes"],
            results["Minimax"]["nodes"],
        )

    def test_captures_hanging_queen(self):
        board, moves, _, turn = self.play_moves([
            "e2e4", "e7e5",
            "g1f3", "d8g5",
        ])
        best = self.ai.find_best_move(board, moves, turn, depth=2)
        self.assertEqual(best, "f3g5")

    def test_make_move_promotion_and_undo_sync(self):
        board_before = [["." for _ in range(8)] for _ in range(8)]
        board_before[1][0] = "P"
        board_before[6][1] = "p"
        w_promo = make_move(board_before, "a7a8q")
        b_promo = make_move(board_before, "b2b1n")
        self.assertEqual(w_promo[0][0], "Q")
        self.assertEqual(b_promo[7][1], "n")

        self.play_moves(["e2e4", "e7e5"])
        self.ai.undo_move()
        _, _, _, turn_after = get_position(self.engine)
        self.assertEqual(turn_after, "BLACK")


if __name__ == "__main__":
    unittest.main()
