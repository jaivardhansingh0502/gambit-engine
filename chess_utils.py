import threading

try:
    import winsound
except ImportError:
    winsound = None


STANDARD_START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

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
