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