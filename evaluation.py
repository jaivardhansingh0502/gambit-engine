PIECE_VALUES = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,

    'p': -1,
    'n': -3,
    'b': -3,
    'r': -5,
    'q': -9
}

AI_PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,

    'p': -100,
    'n': -320,
    'b': -330,
    'r': -500,
    'q': -900
}


PAWN_TABLE = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5,  5, 10, 25, 25, 10,  5,  5],
    [0,  0,  0, 22, 22,  0,  0,  0],
    [5, -5,-10,  0,  0,-10, -5,  5],
    [5, 10, 10,-20,-20, 10, 10,  5],
    [0,  0,  0,  0,  0,  0,  0,  0]
]

KNIGHT_TABLE = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]

BISHOP_TABLE = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
]

ROOK_TABLE = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [5, 10, 10, 10, 10, 10, 10,  5],
    [-5, 0,  0,  0,  0,  0,  0, -5],
    [-5, 0,  0,  0,  0,  0,  0, -5],
    [-5, 0,  0,  0,  0,  0,  0, -5],
    [-5, 0,  0,  0,  0,  0,  0, -5],
    [-5, 0,  0,  0,  0,  0,  0, -5],
    [0,  0,  0,  5,  5,  0,  0,  0]
]

QUEEN_TABLE = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [-5,   0,  5,  5,  5,  5,  0, -5],
    [0,    0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20]
]

KING_MIDDLE_TABLE = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [20,  20,  0,  0,  0,  0, 20, 20],
    [20,  30, 10,  0,  0, 10, 30, 20]
]

KING_END_TABLE = [
    [-50,-40,-30,-20,-20,-30,-40,-50],
    [-30,-20,-10,  0,  0,-10,-20,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-30,  0,  0,  0,  0,-30,-30],
    [-50,-30,-30,-30,-30,-30,-30,-50]
]

WHITE_PST = {
    'P': PAWN_TABLE,
    'N': KNIGHT_TABLE,
    'B': BISHOP_TABLE,
    'R': ROOK_TABLE,
    'Q': QUEEN_TABLE,
}


def evaluate_board(board):
    """Evaluate position in centipawns from White's perspective."""
    score = 0
    non_king_material = 0
    white_bishops = 0
    black_bishops = 0
    white_king = None
    black_king = None

    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece in ('.', ' '):
                continue

            val = AI_PIECE_VALUES.get(piece, 0)
            score += val
            if piece not in ('K', 'k'):
                non_king_material += abs(val)

            if piece == 'B':
                white_bishops += 1
            elif piece == 'b':
                black_bishops += 1
            elif piece == 'K':
                white_king = (row, col)
            elif piece == 'k':
                black_king = (row, col)

            if piece in WHITE_PST:
                score += WHITE_PST[piece][row][col]
            else:
                upper = piece.upper()
                if upper in WHITE_PST:
                    score -= WHITE_PST[upper][7 - row][col]

    # Bishop pair bonus
    if white_bishops >= 2:
        score += 30
    if black_bishops >= 2:
        score -= 30

    # King placement: safety in middlegame, centralization in endgame
    king_table = KING_END_TABLE if non_king_material <= 2600 else KING_MIDDLE_TABLE
    if white_king is not None:
        score += king_table[white_king[0]][white_king[1]]
    if black_king is not None:
        score -= king_table[7 - black_king[0]][black_king[1]]

    return score


PIECE_ORDER = ('Q', 'R', 'B', 'N', 'P')

PIECE_NAMES = {
    'Q': ('queen', 'queens'),
    'R': ('rook', 'rooks'),
    'B': ('bishop', 'bishops'),
    'N': ('knight', 'knights'),
    'P': ('pawn', 'pawns'),
}


def _format_piece_list(items):
    """Format a list of (piece_key, count) pairs into natural English."""
    phrases = []
    for piece_key, count in items:
        singular, plural = PIECE_NAMES[piece_key]
        if count == 1:
            phrases.append(f"a {singular}")
        else:
            phrases.append(f"{count} {plural}")

    if len(phrases) == 1:
        return phrases[0]
    if len(phrases) == 2:
        return f"{phrases[0]} and {phrases[1]}"
    return ", ".join(phrases[:-1]) + f", and {phrases[-1]}"


def analyze_material(board):
    """Return White/Black piece counts, material score from White's perspective, and an explanation."""
    white_counts = {k: 0 for k in PIECE_ORDER}
    black_counts = {k: 0 for k in PIECE_ORDER}

    for row in board:
        for piece in row:
            if piece in white_counts:
                white_counts[piece] += 1
            elif piece.upper() in black_counts and piece.islower():
                black_counts[piece.upper()] += 1

    white_total = sum(white_counts[k] * PIECE_VALUES[k] for k in PIECE_ORDER)
    black_total = sum(black_counts[k] * PIECE_VALUES[k] for k in PIECE_ORDER)
    score = white_total - black_total

    white_extra = []
    black_extra = []
    for k in PIECE_ORDER:
        diff = white_counts[k] - black_counts[k]
        if diff > 0:
            white_extra.append((k, diff))
        elif diff < 0:
            black_extra.append((k, -diff))

    if not white_extra and not black_extra:
        explanation = "Material is equal."
    elif white_extra and not black_extra:
        explanation = f"White has an extra {_format_piece_list(white_extra)}."
    elif black_extra and not white_extra:
        explanation = f"Black has an extra {_format_piece_list(black_extra)}."
    else:
        explanation = (
            f"White is ahead {_format_piece_list(white_extra)}; "
            f"Black is ahead {_format_piece_list(black_extra)}."
        )

    return {
        "white_counts": white_counts,
        "black_counts": black_counts,
        "white_total": white_total,
        "black_total": black_total,
        "score": score,
        "explanation": explanation,
    }


def format_evaluation_summary(score, threshold=0.25):
    """Return (display_text, side, hex_color) from White's perspective."""
    if score >= threshold:
        return f"White is better: +{score:.1f}", "WHITE", "#15803D"
    if score <= -threshold:
        return f"Black is better: {score:.1f}", "BLACK", "#B91C1C"
    return "Position is equal: 0.0", "EQUAL", "#374151"