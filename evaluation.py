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


KNIGHT_TABLE = [
    [-5, -4, -3, -3, -3, -3, -4, -5],
    [-4, -2,  0,  0,  0,  0, -2, -4],
    [-3,  0,  1,  2,  2,  1,  0, -3],
    [-3,  1,  2,  3,  3,  2,  1, -3],
    [-3,  1,  2,  3,  3,  2,  1, -3],
    [-3,  0,  1,  2,  2,  1,  0, -3],
    [-4, -2,  0,  0,  0,  0, -2, -4],
    [-5, -4, -3, -3, -3, -3, -4, -5]
]


PAWN_TABLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 5, 5, 5, 5, 5, 5, 5],
    [2, 2, 2, 3, 3, 2, 2, 2],
    [1, 1, 2, 3, 3, 2, 1, 1],
    [0, 0, 1, 2, 2, 1, 0, 0],
    [0, 0, 0, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0]
]


def evaluate_board(board):

    score = 0

    for row in range(8):
        for col in range(8):

            piece = board[row][col]

            score += PIECE_VALUES.get(piece, 0)

            if piece == 'N':
                score += KNIGHT_TABLE[row][col]

            elif piece == 'n':
                score -= KNIGHT_TABLE[7 - row][col]

            elif piece == 'P':
                score += PAWN_TABLE[row][col]

            elif piece == 'p':
                score -= PAWN_TABLE[7 - row][col]

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