from evaluation import evaluate_board


def make_move(board, move):

    new_board = [row[:] for row in board]

    start = move[:2]
    end = move[2:]

    start_row = 8 - int(start[1])
    start_col = ord(start[0]) - ord('a')

    end_row = 8 - int(end[1])
    end_col = ord(end[0]) - ord('a')

    new_board[end_row][end_col] = new_board[start_row][start_col]
    new_board[start_row][start_col] = ' '

    return new_board

class AI:

    def __init__(self):
        pass

    def find_best_move(self, board, legal_moves):

        if not legal_moves:
            return None

        score = evaluate_board(board)

        print("Current evaluation:", score)

        return legal_moves[0]


if __name__ == "__main__":

    ai = AI()

    board = [
        ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
        ['p', 'p', 'p', 'p', 'p', 'p', 'p', ' '],
        [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
        [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
        [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
        [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
        ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
        ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
    ]

    legal_moves = [
        "e2e4",
        "d2d4",
        "g1f3"
    ]

    move = ai.find_best_move(board, legal_moves)

    print("AI selected:", move)