import math
import threading

try:
    import winsound
except ImportError:
    winsound = None


STANDARD_START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

OPENING_LINES = [
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5a4", "g8f6", "e1g1", "f8e7"), "Ruy Lopez: Closed Morphy"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6", "b5c6"), "Ruy Lopez: Exchange Variation"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "g8f6"), "Ruy Lopez: Berlin Defense"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "a7a6"), "Ruy Lopez: Morphy Defense"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1b5"), "Ruy Lopez"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "b2b4"), "Italian Game: Evans Gambit"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5"), "Italian Game: Giuoco Piano"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "f3g5"), "Italian Game: Fried Liver Attack"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6"), "Italian Game: Two Knights"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "f1c4"), "Italian Game"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "d2d4", "e5d4", "f3d4"), "Scotch Game"),
    (("e2e4", "e7e5", "g1f3", "b8c6", "d2d4"), "Scotch Opening"),
    (("e2e4", "e7e5", "g1f3", "g8f6"), "Petroff Defense"),
    (("e2e4", "e7e5", "g1f3", "d7d6"), "Philidor Defense"),
    (("e2e4", "e7e5", "b1c3"), "Vienna Game"),
    (("e2e4", "e7e5", "f2f4"), "King's Gambit"),
    (("e2e4", "e7e5", "f1c4"), "Bishop's Opening"),
    (("e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "a7a6"), "Sicilian Defense: Najdorf"),
    (("e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "g7g6"), "Sicilian Defense: Dragon"),
    (("e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "b8c6"), "Sicilian Defense: Classical"),
    (("e2e4", "c7c5", "g1f3", "e7e6", "d2d4", "c5d4", "f3d4", "b8c6"), "Sicilian Defense: Taimanov"),
    (("e2e4", "c7c5", "g1f3", "b8c6", "d2d4", "c5d4", "f3d4", "g7g6"), "Sicilian: Accelerated Dragon"),
    (("e2e4", "c7c5", "g1f3", "b8c6", "f1b5"), "Sicilian Defense: Rossolimo"),
    (("e2e4", "c7c5", "c2c3"), "Sicilian Defense: Alapin"),
    (("e2e4", "c7c5"), "Sicilian Defense"),
    (("e2e4", "e7e6", "d2d4", "d7d5", "b1c3", "f8b4"), "French Defense: Winawer"),
    (("e2e4", "e7e6", "d2d4", "d7d5", "b1c3", "g8f6"), "French Defense: Classical"),
    (("e2e4", "e7e6", "d2d4", "d7d5", "b1d2"), "French Defense: Tarrasch"),
    (("e2e4", "e7e6", "d2d4", "d7d5", "e4e5"), "French Defense: Advance"),
    (("e2e4", "e7e6"), "French Defense"),
    (("e2e4", "c7c6", "d2d4", "d7d5", "b1c3", "d5e4", "c3e4", "c8f5"), "Caro-Kann: Classical"),
    (("e2e4", "c7c6", "d2d4", "d7d5", "e4e5"), "Caro-Kann: Advance"),
    (("e2e4", "c7c6", "d2d4", "d7d5", "e4d5", "c6d5", "c2c4"), "Caro-Kann: Panov Attack"),
    (("e2e4", "c7c6"), "Caro-Kann Defense"),
    (("e2e4", "d7d5"), "Scandinavian Defense"),
    (("e2e4", "d7d6", "d2d4", "g8f6", "b1c3", "g7g6"), "Pirc Defense"),
    (("e2e4", "g8f6"), "Alekhine's Defense"),
    (("e2e4", "g7g6"), "Modern Defense"),
    (("e2e4", "e7e5"), "Open Game"),
    (("e2e4",), "King's Pawn Opening"),
    (("d2d4", "d7d5", "c2c4", "c7c6", "g1f3", "g8f6", "b1c3", "e7e6"), "Semi-Slav Defense"),
    (("d2d4", "d7d5", "c2c4", "c7c6"), "Slav Defense"),
    (("d2d4", "d7d5", "c2c4", "d5c4"), "Queen's Gambit Accepted"),
    (("d2d4", "d7d5", "c2c4", "e7e6"), "Queen's Gambit Declined"),
    (("d2d4", "d7d5", "c2c4"), "Queen's Gambit"),
    (("d2d4", "d7d5", "c1f4"), "London System"),
    (("d2d4", "g8f6", "c2c4", "e7e6", "g2g3"), "Catalan Opening"),
    (("d2d4", "g8f6", "c2c4", "e7e6", "b1c3", "f8b4"), "Nimzo-Indian Defense"),
    (("d2d4", "g8f6", "c2c4", "e7e6", "g1f3", "b7b6"), "Queen's Indian Defense"),
    (("d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "d7d5"), "Grunfeld Defense"),
    (("d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "f8g7", "e2e4"), "King's Indian Defense"),
    (("d2d4", "g8f6", "c2c4", "c7c5", "d4d5"), "Benoni Defense"),
    (("d2d4", "f7f5"), "Dutch Defense"),
    (("d2d4", "g8f6"), "Indian Defense"),
    (("d2d4", "d7d5"), "Closed Game"),
    (("d2d4",), "Queen's Pawn Opening"),
    (("c2c4", "e7e5"), "English: Reversed Sicilian"),
    (("c2c4", "c7c5"), "English: Symmetrical"),
    (("c2c4",), "English Opening"),
    (("g1f3", "d7d5", "c2c4"), "Reti Opening"),
    (("g1f3",), "Reti / Zukertort Opening"),
    (("g2g3",), "King's Fianchetto / Benko"),
    (("f2f4",), "Bird's Opening"),
]
OPENING_LINES.sort(key=lambda item: -len(item[0]))


def detect_opening_name(move_history, initial_fen=STANDARD_START_FEN):
    """Return the most specific known opening name matching move_history."""
    if initial_fen and initial_fen != STANDARD_START_FEN:
        return "Custom FEN Position"
    if not move_history:
        return "Starting Position"
    seq = tuple(m[:4].lower() for m in move_history)
    for prefix, name in OPENING_LINES:
        if len(seq) >= len(prefix) and seq[:len(prefix)] == prefix:
            return name
    return "Unclassified Opening"


def classify_cp_loss(cp_loss, is_best_move=False):
    """Classify centipawn loss into (symbol, label) for Move History."""
    loss = max(0, int(cp_loss))
    if is_best_move or loss <= 10:
        return ("!", "Best")
    if loss <= 60:
        return ("", "Good")
    if loss <= 140:
        return ("?!", "Inaccuracy")
    if loss <= 299:
        return ("?", "Mistake")
    return ("??", "Blunder")


def calculate_accuracy(cp_losses):
    """Return a 0-100 accuracy score from a sequence of centipawn losses."""
    if not cp_losses:
        return 100.0
    total = 0.0
    for loss in cp_losses:
        bounded = max(0.0, min(1000.0, float(loss)))
        acc = 103.1668 * math.exp(-0.004 * bounded) - 3.1669
        total += max(0.0, min(100.0, acc))
    return round(total / len(cp_losses), 1)

CAPTURE_ORDER = {"q": 0, "r": 1, "b": 2, "n": 3, "p": 4}
SOLID_GLYPHS = {
    "K": "♚",
    "Q": "♛",
    "R": "♜",
    "B": "♝",
    "N": "♞",
    "P": "♟",
    "k": "♚",
    "q": "♛",
    "r": "♜",
    "b": "♝",
    "n": "♞",
    "p": "♟",
}


def _sq_to_rc(sq):
    return 8 - int(sq[1]), ord(sq[0]) - ord("a")


def get_captured_piece(board_before, move):
    """Return captured piece char for move on board_before, handling en passant."""
    if not board_before or len(move) < 4:
        return None
    sr, sc = _sq_to_rc(move[:2])
    er, ec = _sq_to_rc(move[2:4])
    attacker = board_before[sr][sc]
    target = board_before[er][ec]

    if target not in (".", " "):
        return target
    if attacker in ("P", "p") and sc != ec:
        return "p" if attacker == "P" else "P"
    return None


def format_san_move(board_before, legal_moves, move, next_status="NORMAL"):
    """Format a coordinate move like g1f3/e1g1/e7e8q into SAN."""
    if not board_before or len(move) < 4:
        return move

    sr, sc = _sq_to_rc(move[:2])
    er, ec = _sq_to_rc(move[2:4])
    piece = board_before[sr][sc]
    captured = get_captured_piece(board_before, move)

    suffix = ""
    if next_status == "CHECKMATE":
        suffix = "#"
    elif next_status == "CHECK":
        suffix = "+"

    if piece in ("K", "k") and sc == 4 and ec == 6:
        return "O-O" + suffix
    if piece in ("K", "k") and sc == 4 and ec == 2:
        return "O-O-O" + suffix

    if piece in ("P", "p"):
        base = f"{move[0]}x{move[2:4]}" if captured is not None else move[2:4]
        if len(move) == 5:
            base += f"={move[4].upper()}"
        return base + suffix

    piece_letter = piece.upper()
    others = []
    for candidate in legal_moves:
        if candidate == move or len(candidate) < 4:
            continue
        if candidate[2:4] != move[2:4]:
            continue
        cr, cc = _sq_to_rc(candidate[:2])
        if board_before[cr][cc] == piece:
            others.append(candidate)

    disambig = ""
    if others:
        same_file = any(m[0] == move[0] for m in others)
        same_rank = any(m[1] == move[1] for m in others)
        if not same_file:
            disambig = move[0]
        elif not same_rank:
            disambig = move[1]
        else:
            disambig = move[:2]

    cap_str = "x" if captured is not None else ""
    return f"{piece_letter}{disambig}{cap_str}{move[2:4]}{suffix}"


def format_captured_tray(captured_pieces):
    """Format captured pieces ordered from Queen down to Pawn."""
    if not captured_pieces:
        return "—"
    ordered = sorted(
        captured_pieces,
        key=lambda p: CAPTURE_ORDER.get(p.lower(), 9),
    )
    return " ".join(SOLID_GLYPHS.get(p, p) for p in ordered)


def pgn_result(game_status, white_turn):
    if game_status == "CHECKMATE":
        return "0-1" if white_turn else "1-0"
    if game_status in ("RESIGNED_WHITE", "TIMEOUT_WHITE"):
        return "0-1"
    if game_status in ("RESIGNED_BLACK", "TIMEOUT_BLACK"):
        return "1-0"
    if game_status in (
        "STALEMATE",
        "DRAW_INSUFFICIENT_MATERIAL",
        "DRAW_FIFTY_MOVE",
        "DRAW_THREEFOLD_REPETITION",
        "DRAW_AGREED",
    ):
        return "1/2-1/2"
    return "*"


def build_pgn(
    san_moves,
    game_status,
    white_turn,
    white_name="White",
    black_name="Black",
    initial_fen=None,
):
    result = pgn_result(game_status, white_turn)
    headers = [
        '[Event "Gambit Chess Game"]',
        '[Site "Gambit Desktop"]',
        f'[White "{white_name}"]',
        f'[Black "{black_name}"]',
        f'[Result "{result}"]',
    ]
    if initial_fen and initial_fen != STANDARD_START_FEN:
        headers.append('[SetUp "1"]')
        headers.append(f'[FEN "{initial_fen}"]')

    tokens = []
    for i in range(0, len(san_moves), 2):
        move_num = (i // 2) + 1
        if i + 1 < len(san_moves):
            tokens.append(f"{move_num}. {san_moves[i]} {san_moves[i + 1]}")
        else:
            tokens.append(f"{move_num}. {san_moves[i]}")
    tokens.append(result)

    return "\n".join(headers) + "\n\n" + " ".join(tokens)


def play_sound(kind, enabled=True):
    if not enabled or winsound is None:
        return

    tones = {
        "move": (520, 35),
        "capture": (680, 50),
        "castle": (580, 45),
        "check": (880, 70),
        "gameover": (420, 110),
    }
    freq, dur = tones.get(kind, (500, 35))

    def _beep():
        try:
            winsound.Beep(freq, dur)
        except Exception:
            pass

    threading.Thread(target=_beep, daemon=True).start()
