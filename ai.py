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

        best_move = None
        best_score = float('-inf')

        for move in legal_moves:

            new_board = make_move(board, move)

            score = evaluate_board(new_board)

            print(move, "->", score)

            if score > best_score:
                best_score = score
                best_move = move
        return best_move


if __name__ == "__main__":

    ai = AI()

    board = [
    [' ', ' ', ' ', ' ', 'k', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', 'p', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' '],
    [' ', ' ', ' ', ' ', 'R', ' ', ' ', 'K']
]


    legal_moves = [
    "e1e2",
    "e1e7"
]

    move = ai.find_best_move(board, legal_moves)

    print("AI selected:", move)