import os
import sys
import tempfile
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from chess_utils import (
    STANDARD_START_FEN,
    build_pgn,
    calculate_accuracy,
    classify_cp_loss,
    detect_opening_name,
    format_captured_tray,
    format_san_move,
    generate_app_icon,
    get_captured_piece,
    load_user_settings,
    parse_custom_time_control,
    pgn_result,
    play_sound,
    resolve_time_control_spec,
    save_user_settings,
)


def empty_board():
    return [["." for _ in range(8)] for _ in range(8)]


def initial_board():
    return [
        list("rnbqkbnr"),
        list("pppppppp"),
        list("........"),
        list("........"),
        list("........"),
        list("........"),
        list("PPPPPPPP"),
        list("RNBQKBNR"),
    ]


class ChessUtilsTests(unittest.TestCase):
    def test_san_opening_castling_and_check_suffixes(self):
        board = initial_board()
        legal = ["e2e4", "g1f3", "b1c3"]
        self.assertEqual(format_san_move(board, legal, "e2e4"), "e4")
        self.assertEqual(format_san_move(board, legal, "g1f3", next_status="CHECK"), "Nf3+")

        b2 = empty_board()
        b2[7][4] = "K"
        b2[7][7] = "R"
        b2[7][0] = "R"
        b2[0][4] = "k"
        self.assertEqual(format_san_move(b2, ["e1g1", "e1c1"], "e1g1"), "O-O")
        self.assertEqual(
            format_san_move(b2, ["e1g1", "e1c1"], "e1c1", next_status="CHECKMATE"),
            "O-O-O#",
        )

    def test_san_disambiguation_captures_ep_and_promotion(self):
        # Two White knights on c3 and g1 both able to reach e2 -> file disambiguation Ncxe2 / Nce2
        b = empty_board()
        b[7][4] = "K"
        b[0][4] = "k"
        b[5][2] = "N"  # c3
        b[7][6] = "N"  # g1
        b[6][4] = "p"  # e2
        legal = ["c3e2", "g1e2"]
        self.assertEqual(format_san_move(b, legal, "c3e2"), "Ncxe2")

        # Same file Knights c3 and c1 reaching e2 -> rank disambiguation
        b3 = empty_board()
        b3[7][4] = "K"
        b3[0][4] = "k"
        b3[5][2] = "N"  # c3
        b3[7][2] = "N"  # c1
        self.assertEqual(format_san_move(b3, ["c3e2", "c1e2"], "c3e2"), "N3e2")

        # En passant capture (e5 pawn captures diagonally onto empty d6)
        ep_board = empty_board()
        ep_board[7][4] = "K"
        ep_board[0][4] = "k"
        ep_board[3][4] = "P"  # e5
        ep_board[3][3] = "p"  # d5
        self.assertEqual(get_captured_piece(ep_board, "e5d6"), "p")
        self.assertEqual(format_san_move(ep_board, ["e5d6"], "e5d6"), "exd6")

        # Capture + promotion + check
        promo = empty_board()
        promo[7][4] = "K"
        promo[0][4] = "k"
        promo[1][0] = "P"  # a7
        promo[0][1] = "r"  # b8
        self.assertEqual(get_captured_piece(promo, "a7b8q"), "r")
        self.assertEqual(
            format_san_move(promo, ["a7b8q"], "a7b8q", next_status="CHECK"),
            "axb8=Q+",
        )

    def test_captured_tray_formatting_and_advantage(self):
        self.assertEqual(format_captured_tray([]), "—")
        tray = format_captured_tray(["p", "q", "n", "p"])
        # Sorted high value first: q, n, p, p -> Black pieces captured by White
        self.assertEqual(tray, "♛ ♞ ♟ ♟")

    def test_pgn_result_and_export(self):
        self.assertEqual(pgn_result("CHECKMATE", True), "0-1")
        self.assertEqual(pgn_result("CHECKMATE", False), "1-0")
        self.assertEqual(pgn_result("DRAW_FIFTY_MOVE", True), "1/2-1/2")
        self.assertEqual(pgn_result("DRAW_AGREED", False), "1/2-1/2")
        self.assertEqual(pgn_result("NORMAL", True), "*")

        pgn = build_pgn(
            ["e4", "e5", "Qh5", "Nc6", "Bc4", "Nf6", "Qxf7#"],
            "CHECKMATE",
            False,
            white_name="Player 1",
            black_name="Gambit AI",
            initial_fen=STANDARD_START_FEN,
        )
        self.assertIn('[Result "1-0"]', pgn)
        self.assertIn("1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0", pgn)

        custom_pgn = build_pgn(
            ["Kh1"],
            "DRAW_AGREED",
            True,
            initial_fen="4k3/8/8/8/8/8/8/4K2R w - - 99 1",
        )
        self.assertIn('[SetUp "1"]', custom_pgn)
        self.assertIn('[FEN "4k3/8/8/8/8/8/8/4K2R w - - 99 1"]', custom_pgn)

    def test_play_sound_safe_when_disabled(self):
        play_sound("move", enabled=False)
        play_sound("capture", enabled=False)
        play_sound("unknown", enabled=False)

    def test_opening_detection_cp_classification_and_accuracy(self):
        self.assertEqual(detect_opening_name([]), "Starting Position")
        self.assertEqual(detect_opening_name(["e2e4"]), "King's Pawn Opening")
        self.assertEqual(
            detect_opening_name(["e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "a7a6"]),
            "Sicilian Defense: Najdorf",
        )
        self.assertEqual(
            detect_opening_name(["e2e4"], initial_fen="4k3/8/8/8/8/8/8/4K3 w - - 0 1"),
            "Custom FEN Position",
        )

        self.assertEqual(classify_cp_loss(0, is_best_move=True), ("!", "Best"))
        self.assertEqual(classify_cp_loss(35), ("", "Good"))
        self.assertEqual(classify_cp_loss(95), ("?!", "Inaccuracy"))
        self.assertEqual(classify_cp_loss(210), ("?", "Mistake"))
        self.assertEqual(classify_cp_loss(450), ("??", "Blunder"))

        self.assertEqual(calculate_accuracy([]), 100.0)
        self.assertEqual(calculate_accuracy([0, 0]), 100.0)
        mid_acc = calculate_accuracy([20, 80, 350])
        self.assertGreater(mid_acc, 20.0)
        self.assertLess(mid_acc, 95.0)

    def test_custom_time_settings_persistence_and_icon_generation(self):
        label, spec = parse_custom_time_control(7, 5)
        self.assertEqual(label, "Custom (7+5)")
        self.assertEqual(spec, (420, 5))
        self.assertEqual(resolve_time_control_spec("Custom (7+5)"), (420, 5))
        self.assertEqual(resolve_time_control_spec("Blitz (5+3)"), (300, 3))
        with self.assertRaises(ValueError):
            parse_custom_time_control(0, 0)

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = os.path.join(tmpdir, "settings.json")
            defaults = load_user_settings(cfg_path)
            self.assertEqual(defaults["board_theme"], "Classic Green")
            self.assertTrue(
                save_user_settings(
                    {
                        "board_theme": "Slate Blue",
                        "sound_enabled": False,
                        "difficulty": "Hard (Depth 6)",
                        "time_control": "Custom (7+5)",
                    },
                    cfg_path,
                )
            )
            loaded = load_user_settings(cfg_path)
            self.assertEqual(loaded["board_theme"], "Slate Blue")
            self.assertFalse(loaded["sound_enabled"])
            self.assertEqual(loaded["difficulty"], "Hard (Depth 6)")
            self.assertEqual(loaded["time_control"], "Custom (7+5)")

            ico_path = os.path.join(tmpdir, "gambit.ico")
            generate_app_icon(ico_path)
            with open(ico_path, "rb") as f:
                data = f.read()
            self.assertGreater(len(data), 4000)
            self.assertEqual(data[:4], b"\x00\x00\x01\x00")


if __name__ == "__main__":
    unittest.main()
