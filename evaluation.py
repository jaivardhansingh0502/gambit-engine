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


def evaluate_board(board):

    score = 0

    for row in board:
        for piece in row:
            score += PIECE_VALUES.get(piece, 0)

    return score


if __name__ == "__main__":

    board = [
        ['r', 'n', 'b', 'q', 'k', 'b', 'n', ' '],
        ['p', 'p', 'p', 'p', 'p', 'p', 'p', ' '],
        [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
        [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
        [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
        [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
        ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
        ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
    ]

    print("Board Evaluation:", evaluate_board(board))