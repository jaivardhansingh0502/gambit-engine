import os
import subprocess
import sys
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ai import (
    analyze_position_with_engine,
    get_cpp_best_move,
    get_engine_evaluation,
    get_fen,
    get_perft,
    get_position,
    send_move_to_engine,
    set_fen,
)
from evaluation import analyze_material


class GambitEngineTests(unittest.TestCase):
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

    def tearDown(self):
        if self.engine.poll() is None:
            self.engine.terminate()
            self.engine.wait(timeout=3)
        if self.engine.stdin:
            self.engine.stdin.close()
        if self.engine.stdout:
            self.engine.stdout.close()

    def send_raw(self, command):
        self.engine.stdin.write(command + "\n")
        self.engine.stdin.flush()
        return self.engine.stdout.readline().strip()

    def play_moves(self, moves):
        for move in moves:
            resp = send_move_to_engine(self.engine, move)
            self.assertEqual(resp, "MOVE_OK", f"Expected MOVE_OK for {move}, got {resp}")
        return get_position(self.engine)

    def test_initial_position_and_protocol(self):
        board, moves, status, turn = get_position(self.engine)
        self.assertEqual(len(board), 8)
        self.assertEqual(len(moves), 20)
        self.assertEqual(status, "NORMAL")
        self.assertEqual(turn, "WHITE")
        self.assertEqual("".join(board[0]), "rnbqkbnr")
        self.assertEqual("".join(board[7]), "RNBQKBNR")

    def test_invalid_and_malformed_moves(self):
        self.assertEqual(send_move_to_engine(self.engine, "e2e5"), "MOVE_INVALID")
        self.assertEqual(send_move_to_engine(self.engine, "e2"), "MOVE_INVALID")
        self.assertEqual(send_move_to_engine(self.engine, "e2e4x"), "MOVE_INVALID")
        self.assertEqual(send_move_to_engine(self.engine, "e2e4qq"), "MOVE_INVALID")

    def test_undo_and_new_game(self):
        self.assertEqual(self.send_raw("UNDO_MOVE"), "UNDO_EMPTY")

        self.play_moves(["e2e4", "e7e5"])
        self.assertEqual(self.send_raw("UNDO_MOVE"), "UNDO_OK")
        _, _, _, turn = get_position(self.engine)
        self.assertEqual(turn, "BLACK")

        self.assertEqual(self.send_raw("NEW_GAME"), "NEW_GAME_OK")
        self.assertEqual(self.send_raw("UNDO_MOVE"), "UNDO_EMPTY")
        _, moves, status, turn = get_position(self.engine)
        self.assertEqual(len(moves), 20)
        self.assertEqual(status, "NORMAL")
        self.assertEqual(turn, "WHITE")

    def test_kingside_and_queenside_castling(self):
        # White kingside castling (e1g1), Black queenside castling (e8c8)
        board, _, status, turn = self.play_moves([
            "e2e4", "d7d5",
            "f1e2", "b8c6",
            "g1f3", "c8f5",
            "e1g1", "d8d7",
            "d2d3", "e8c8",
        ])
        self.assertEqual(status, "NORMAL")
        self.assertEqual(turn, "WHITE")
        self.assertEqual(board[7][6], "K")
        self.assertEqual(board[7][5], "R")
        self.assertEqual(board[0][2], "k")
        self.assertEqual(board[0][3], "r")

    def test_en_passant_capture(self):
        board, moves, _, turn = self.play_moves([
            "e2e4", "a7a6",
            "e4e5", "d7d5",
        ])
        self.assertEqual(turn, "WHITE")
        self.assertIn("e5d6", moves)

        board, _, _, turn = self.play_moves(["e5d6"])
        self.assertEqual(turn, "BLACK")
        self.assertEqual(board[2][3], "P")  # d6
        self.assertEqual(board[3][3], ".")  # d5 captured

    def test_under_promotion_preserved(self):
        board, moves, _, turn = self.play_moves([
            "a2a4", "b7b5",
            "a4b5", "a7a6",
            "b5a6", "c7c6",
            "a6a7", "d7d6",
        ])
        self.assertEqual(turn, "WHITE")
        self.assertIn("a7b8n", moves)

        board, _, _, turn = self.play_moves(["a7b8n"])
        self.assertEqual(turn, "BLACK")
        self.assertEqual(board[0][1], "N")  # b8 has promoted Knight

    def test_checkmate_and_game_over_guard(self):
        _, moves, status, turn = self.play_moves([
            "f2f3", "e7e5",
            "g2g4", "d8h4",
        ])
        self.assertEqual(status, "CHECKMATE")
        self.assertEqual(turn, "WHITE")
        self.assertEqual(moves, [])
        self.assertEqual(send_move_to_engine(self.engine, "e2e4"), "GAME_OVER")

    def test_evaluate_command_tracks_captures_and_promotions(self):
        self.assertEqual(get_engine_evaluation(self.engine), 0)

        board, _, _, _ = self.play_moves(["e2e4", "d7d5", "e4d5"])
        self.assertEqual(get_engine_evaluation(self.engine), 1)
        self.assertEqual(get_engine_evaluation(self.engine), analyze_material(board)["score"])

        board, _, _, _ = self.play_moves(["d8d5"])
        self.assertEqual(get_engine_evaluation(self.engine), 0)

        self.send_raw("NEW_GAME")
        board, _, _, _ = self.play_moves([
            "a2a4", "b7b5",
            "a4b5", "a7a6",
            "b5a6", "c7c6",
            "a6a7", "d7d6",
            "a7b8q",
        ])
        expected_score = analyze_material(board)["score"]
        self.assertGreater(expected_score, 0)
        self.assertEqual(get_engine_evaluation(self.engine), expected_score)

    def test_fen_roundtrip_and_invalid_fen(self):
        start_fen = get_fen(self.engine)
        self.assertEqual(
            start_fen,
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        )

        custom_fen = "4k3/8/8/8/8/8/4P3/4K2R w K - 4 20"
        self.assertTrue(set_fen(self.engine, custom_fen))
        self.assertEqual(get_fen(self.engine), custom_fen)

        board, moves, status, turn = get_position(self.engine)
        self.assertEqual(status, "NORMAL")
        self.assertEqual(turn, "WHITE")
        self.assertEqual(board[7][4], "K")
        self.assertEqual(board[7][7], "R")
        self.assertIn("e1g1", moves)

        self.assertFalse(set_fen(self.engine, "invalid fen string"))
        self.assertEqual(get_fen(self.engine), custom_fen)

    def test_fifty_move_and_threefold_repetition_draws(self):
        # 50-move rule: halfmove clock at 99 -> quiet rook move triggers 100
        self.assertTrue(
            set_fen(self.engine, "4k3/8/8/8/8/8/8/4K2R w - - 99 50")
        )
        board, moves, status, turn = self.play_moves(["h1g1"])
        self.assertEqual(status, "DRAW_FIFTY_MOVE")
        self.assertEqual(turn, "BLACK")
        self.assertEqual(moves, [])
        self.assertEqual(board[7][6], "R")
        self.assertEqual(send_move_to_engine(self.engine, "e8d8"), "GAME_OVER")

        # Threefold repetition from initial position (3rd occurrence triggers draw)
        self.assertEqual(self.send_raw("NEW_GAME"), "NEW_GAME_OK")
        _, moves, status, _ = self.play_moves([
            "g1f3", "g8f6",
            "f3g1", "f6g8",
            "g1f3", "g8f6",
            "f3g1", "f6g8",
        ])
        self.assertEqual(status, "DRAW_THREEFOLD_REPETITION")
        self.assertEqual(moves, [])
        self.assertEqual(send_move_to_engine(self.engine, "e2e4"), "GAME_OVER")

    def test_cpp_best_move_tactics_and_state_integrity(self):
        # Scholar's mate in 1: Qxf7#
        mate_fen = "r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4"
        self.assertTrue(set_fen(self.engine, mate_fen))
        best_move, score, nodes = get_cpp_best_move(self.engine, depth=4, time_limit_ms=1000)
        self.assertEqual(best_move, "h5f7")
        self.assertGreater(score, 50000)
        self.assertGreater(nodes, 0)
        # Engine board must stay intact after search
        self.assertEqual(get_fen(self.engine), mate_fen)

    def test_opening_book_black_mate_sign_and_endgame_search(self):
        # 1. Opening book returns classic move instantaneously (1 node) across varied systems
        best_open, open_score, open_nodes = get_cpp_best_move(self.engine, depth=5, time_limit_ms=1000)
        self.assertIn(best_open, {"e2e4", "d2d4", "c2c4", "g1f3", "g2g3"})
        self.assertEqual(open_score, 0)
        self.assertEqual(open_nodes, 1)

        book_probes = [
            (["e2e4"], {"e7e5", "c7c5", "e7e6", "c7c6", "d7d5", "d7d6", "g8f6", "g7g6"}),
            (["e2e4", "e7e5", "g1f3"], {"b8c6", "g8f6", "d7d6"}),
            (["e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3"], {"a7a6", "g7g6", "b8c6"}),
            (["e2e4", "e7e6", "d2d4", "d7d5"], {"b1c3", "b1d2", "e4e5"}),
            (["e2e4", "d7d5"], {"e4d5"}),
            (["d2d4", "d7d5", "c2c4"], {"e7e6", "c7c6", "d5c4"}),
            (["d2d4", "g8f6", "c2c4", "g7g6", "b1c3"], {"f8g7", "d7d5"}),
            (["d2d4", "f7f5"], {"g2g3"}),
            (["c2c4"], {"e7e5", "c7c5", "g8f6"}),
        ]
        for setup_moves, expected_replies in book_probes:
            self.assertEqual(self.send_raw("NEW_GAME"), "NEW_GAME_OK")
            self.play_moves(setup_moves)
            reply, _, reply_nodes = get_cpp_best_move(self.engine, depth=5, time_limit_ms=1000)
            self.assertIn(reply, expected_replies, f"Unexpected reply {reply} after {setup_moves}")
            self.assertEqual(reply_nodes, 1, f"Expected book hit for {setup_moves}")

        # 2. Black mate-in-1 (Fool's mate) returns White-perspective negative mate score
        fools_fen = "rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2"
        self.assertTrue(set_fen(self.engine, fools_fen))
        black_mate, mate_score, mate_nodes = get_cpp_best_move(self.engine, depth=4, time_limit_ms=1000)
        self.assertEqual(black_mate, "d8h4")
        self.assertLess(mate_score, -50000)
        self.assertGreater(mate_nodes, 0)

        # 3. K+P vs K endgame search runs deep cleanly without null-move zugzwang glitches
        kp_fen = "4k3/8/8/4K3/4P3/8/8/8 w - - 0 1"
        self.assertTrue(set_fen(self.engine, kp_fen))
        kp_move, kp_score, kp_nodes = get_cpp_best_move(self.engine, depth=7, time_limit_ms=1500)
        self.assertIn(kp_move, {"e5d6", "e5f6"})
        self.assertGreater(kp_score, 100)
        self.assertGreater(kp_nodes, 10)

        # 4. ANALYZE_MOVE skips opening book and searches starting board directly
        self.assertEqual(self.send_raw("NEW_GAME"), "NEW_GAME_OK")
        amv, _, anodes = analyze_position_with_engine(self.engine, depth=3, time_limit_ms=500)
        self.assertIsNotNone(amv)
        self.assertGreater(anodes, 1)

    def test_perft_node_counts_across_standard_positions(self):
        # Initial position Perft(1..3)
        start_fen = get_fen(self.engine)
        self.assertEqual(get_perft(self.engine, 1), 20)
        self.assertEqual(get_perft(self.engine, 2), 400)
        self.assertEqual(get_perft(self.engine, 3), 8902)
        self.assertEqual(get_fen(self.engine), start_fen)

        # Kiwipete (castling, promotions, captures, discovered checks)
        kiwi = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
        self.assertTrue(set_fen(self.engine, kiwi))
        self.assertEqual(get_perft(self.engine, 1), 48)
        self.assertEqual(get_perft(self.engine, 2), 2039)

        # Position 3 (en passant pins & discovered checks)
        pos3 = "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"
        self.assertTrue(set_fen(self.engine, pos3))
        self.assertEqual(get_perft(self.engine, 1), 14)
        self.assertEqual(get_perft(self.engine, 2), 191)
        self.assertEqual(get_perft(self.engine, 3), 2812)

        # Position 4 (promotions & castling)
        pos4 = "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1"
        self.assertTrue(set_fen(self.engine, pos4))
        self.assertEqual(get_perft(self.engine, 1), 6)
        self.assertEqual(get_perft(self.engine, 2), 264)

    def test_uci_protocol_handshake_position_and_go(self):
        uci_proc = subprocess.Popen(
            [os.path.join(ROOT_DIR, "gambit.exe")],
            cwd=ROOT_DIR,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        try:
            uci_script = (
                "uci\n"
                "isready\n"
                "ucinewgame\n"
                "position startpos moves e2e4 c7c5\n"
                "go depth 3\n"
                "position fen r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4\n"
                "go movetime 250\n"
                "quit\n"
            )
            out, _ = uci_proc.communicate(uci_script, timeout=8)
        finally:
            if uci_proc.poll() is None:
                uci_proc.terminate()
                uci_proc.wait(timeout=2)

        self.assertEqual(uci_proc.returncode, 0)
        self.assertIn("id name Gambit Chess Engine", out)
        self.assertIn("uciok", out)
        self.assertIn("readyok", out)
        self.assertIn("bestmove h5f7", out)


if __name__ == "__main__":
    unittest.main()
