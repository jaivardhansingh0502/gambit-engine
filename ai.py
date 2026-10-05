from evaluation import evaluate_board
import subprocess


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


def send_move_to_engine(engine, move):

    print("\nSending move:", move)

    engine.stdin.write(f"MAKE_MOVE {move}\n")
    engine.stdin.flush()

    print("Waiting for engine response...")

    response = engine.stdout.readline().strip()

    print("Response received")

    return response


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

    def minimax(self, board, legal_moves, depth, maximizing_player):

        if depth == 0:
            return evaluate_board(board)

        if maximizing_player:

            best_score = float('-inf')

            for move in legal_moves:

                new_board = make_move(board, move)

                score = self.minimax(
                    new_board,
                    [],
                    depth - 1,
                    False
                )

                best_score = max(best_score, score)

            return best_score

        else:

            best_score = float('inf')

            for move in legal_moves:

                new_board = make_move(board, move)

                score = self.minimax(
                    new_board,
                    [],
                    depth - 1,
                    True
                )

                best_score = min(best_score, score)

            return best_score


if __name__ == "__main__":

    engine = subprocess.Popen(
        ["gambit.exe"],
        stdout=subprocess.PIPE,
        stdin=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )

    # Ask C++ for the initial position
    engine.stdin.write("GET_MOVES\n")
    engine.stdin.flush()

    board = []
    legal_moves = []

    section = None

    while True:

        line = engine.stdout.readline().strip()

        if not line:
            continue

        if line == "BOARD":
            section = "board"
            continue

        if line == "MOVES":
            section = "moves"
            continue

        if line == "END":
            break

        if section == "board":
            board.append(list(line))

        elif section == "moves":
            legal_moves.append(line)

    print("Board received:")

    for row in board:
        print(row)

    print("\nLegal moves received:")

    for move in legal_moves:
        print(move)

    # Test communication with C++
    response = send_move_to_engine(
        engine,
        "e2e4"
    )

    print("\nEngine response:", response)

    ai = AI()

    best_move = ai.find_best_move(
        board,
        legal_moves
    )

    print("\nAI selected:", best_move)

    engine.terminate()