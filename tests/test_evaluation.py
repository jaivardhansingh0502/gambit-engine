import os
import sys
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from evaluation import analyze_material, format_evaluation_summary


def empty_board():
    return [["." for _ in range(8)] for _ in range(8)]


class EvaluationTests(unittest.TestCase):
    def test_starting_board_material_is_equal(self):
        board = [
            list("rnbqkbnr"),
            list("pppppppp"),
            list("........"),
            list("........"),
            list("........"),
            list("........"),
            list("PPPPPPPP"),
            list("RNBQKBNR"),
        ]
        result = analyze_material(board)
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["white_total"], 39)
        self.assertEqual(result["black_total"], 39)
        self.assertEqual(result["explanation"], "Material is equal.")

    def test_white_and_black_material_advantage_orientation(self):
        board = empty_board()
        board[7][4] = "K"
        board[0][4] = "k"
        board[6][0] = "P"
        board[5][2] = "B"
        result = analyze_material(board)
        self.assertEqual(result["score"], 4)
        self.assertIn("bishop", result["explanation"])
        self.assertIn("pawn", result["explanation"])

        board_black_ahead = empty_board()
        board_black_ahead[7][4] = "K"
        board_black_ahead[0][4] = "k"
        board_black_ahead[0][0] = "r"
        result_black = analyze_material(board_black_ahead)
        self.assertEqual(result_black["score"], -5)
        self.assertIn("Black has an extra", result_black["explanation"])
        self.assertIn("rook", result_black["explanation"])

    def test_promotion_updates_material_and_kings_excluded(self):
        board = empty_board()
        board[7][4] = "K"
        board[0][4] = "k"
        board[1][0] = "P"
        before = analyze_material(board)
        self.assertEqual(before["score"], 1)

        board[1][0] = "."
        board[0][0] = "Q"
        after = analyze_material(board)
        self.assertEqual(after["score"], 9)

    def test_format_evaluation_summary_threshold_and_signs(self):
        text, side, _ = format_evaluation_summary(2.4)
        self.assertEqual(text, "White is better: +2.4")
        self.assertEqual(side, "WHITE")

        text, side, _ = format_evaluation_summary(-3.1)
        self.assertEqual(text, "Black is better: -3.1")
        self.assertEqual(side, "BLACK")

        text, side, _ = format_evaluation_summary(0.1)
        self.assertEqual(text, "Position is equal: 0.0")
        self.assertEqual(side, "EQUAL")


if __name__ == "__main__":
    unittest.main()
