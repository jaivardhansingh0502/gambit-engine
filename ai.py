from evaluation import evaluate_board

import subprocess



def make_move(board, move):



    new_board = [row[:] for row in board]


    start = move[:2]
    end = move[2:4]




    start_row = 8 - int(start[1])
    start_col = ord(start[0]) - ord('a')




    end_row = 8 - int(end[1])
    end_col = ord(end[0]) - ord('a')




    new_board[end_row][end_col] = new_board[start_row][start_col]
    new_board[start_row][start_col] = ' '




    # Basic promotion support for local board simulation
    if len(move) == 5 and new_board[end_row][end_col] in ('P', 'p'):



        promotion = move[4]



        if new_board[end_row][end_col] == 'P':



            new_board[end_row][end_col] = promotion.upper()



        else:



            new_board[end_row][end_col] = promotion.lower()


    return new_board




def send_move_to_engine(engine, move):



    print("\nSending move:", move)


    engine.stdin.write(f"MAKE_MOVE {move}\n")
    engine.stdin.flush()




    print("Waiting for engine response...")




    response = engine.stdout.readline().strip()




    print("Response received")



    return response




def get_position(engine):

    turn = "WHITE"




    engine.stdin.write("GET_MOVES\n")
    engine.stdin.flush()


    board = []


    legal_moves = []



    status = "NORMAL"
    section = None



    while True:


        line = engine.stdout.readline()


        if line == "":


            raise RuntimeError("C++ engine closed its output.")





        line = line.strip()





        if line == "BOARD":

            section = "board"
            continue




        elif line == "MOVES":

            section = "moves"
            continue




        elif line == "STATUS":

            section = "status"
            continue





        elif line == "TURN":

            section = "turn"
            continue






        elif line == "END":

            break






        if section == "board":

            board.append(list(line))





        elif section == "moves":

            legal_moves.append(line)






        elif section == "status":

            status = line






        elif section == "turn":

            turn = line





    if len(board) != 8 or any(len(row) != 8 for row in board):

        raise RuntimeError("Invalid board received from C++ engine.")




    return board, legal_moves, status, turn




class AI:





    def __init__(self, engine):

        self.engine = engine

        self.nodes_searched = 0




    def undo_move(self):

        self.engine.stdin.write("UNDO_MOVE\n")
        self.engine.stdin.flush()





        response = self.engine.stdout.readline().strip()


        if response != "UNDO_OK":

            raise RuntimeError(f"Undo failed: {response}")






    def find_best_move(self, board, legal_moves, turn):

        self.nodes_searched = 0


        if not legal_moves:

            return None


        white_turn = (turn == "WHITE")


        best_move = None

        best_score = float('-inf') if white_turn else float('inf')


        alpha = float('-inf')
        beta = float('inf')


        for move in legal_moves:


            response = send_move_to_engine(self.engine, move)


            if response != "MOVE_OK":

                raise RuntimeError(
                    f"Engine rejected legal move {move}: {response}"
                )


            try:

                new_board, next_moves, status, next_turn = get_position(
                    self.engine
                )


                score = self.minimax(
                    new_board,
                    next_moves,
                    depth=2,
                    maximizing_player=(next_turn == "WHITE"),
                    alpha=alpha,
                    beta=beta,
                    status=status
                )


            finally:

                self.undo_move()


            print(move, "->", score)


            if white_turn and score > best_score:

                best_score = score
                best_move = move


            elif not white_turn and score < best_score:

                best_score = score
                best_move = move





            # Update alpha-beta bounds across root moves
            if white_turn:

                alpha = max(alpha, best_score)




            else:

                beta = min(beta, best_score)


        print("Nodes searched:", self.nodes_searched)


        return best_move




    def minimax(
        self,
        board,
        legal_moves,
        depth,
        maximizing_player,
        alpha=float('-inf'),
        beta=float('inf'),
        status="NORMAL"
    ):

        self.nodes_searched += 1


        # Terminal positions
        if status == "CHECKMATE":

            return -100000 if maximizing_player else 100000


        if status in ("STALEMATE", "DRAW_INSUFFICIENT_MATERIAL"):

            return 0


        # Leaf node evaluation
        if depth == 0:

            return evaluate_board(board)


        if not legal_moves:

            return evaluate_board(board)




        # Maximizing player: White
        if maximizing_player:

            best_score = float('-inf')


            for move in legal_moves:


                response = send_move_to_engine(self.engine, move)


                if response != "MOVE_OK":

                    raise RuntimeError(
                        f"Engine rejected legal move {move}: {response}"
                    )


                try:

                    new_board, next_moves, next_status, next_turn = (
                        get_position(self.engine)
                    )


                    score = self.minimax(
                        new_board,
                        next_moves,
                        depth - 1,
                        maximizing_player=(next_turn == "WHITE"),
                        alpha=alpha,
                        beta=beta,
                        status=next_status
                    )




                finally:

                    self.undo_move()


                best_score = max(best_score, score)

                alpha = max(alpha, best_score)


                if alpha >= beta:

                    break


            return best_score




        # Minimizing player: Black
        else:

            best_score = float('inf')


            for move in legal_moves:


                response = send_move_to_engine(self.engine, move)


                if response != "MOVE_OK":

                    raise RuntimeError(
                        f"Engine rejected legal move {move}: {response}"
                    )


                try:

                    new_board, next_moves, next_status, next_turn = (
                        get_position(self.engine)
                    )


                    score = self.minimax(
                        new_board,
                        next_moves,
                        depth - 1,
                        maximizing_player=(next_turn == "WHITE"),
                        alpha=alpha,
                        beta=beta,
                        status=next_status
                    )


                finally:

                    self.undo_move()


                best_score = min(best_score, score)

                beta = min(beta, best_score)


                if beta <= alpha:

                    break


            return best_score




if __name__ == "__main__":


    engine = subprocess.Popen(
        ["gambit.exe"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1
    )


    try:

        ai = AI(engine)


        board, legal_moves, status, turn = get_position(engine)


        print("Board received:")

        for row in board:

            print("".join(row))


        print("\nLegal moves:")

        print(legal_moves)


        print("\nGame status:", status)
        print("Turn:", turn)


        if status in (
            "CHECKMATE",
            "STALEMATE",
            "DRAW_INSUFFICIENT_MATERIAL"
        ):

            print("Game has ended.")


        else:

            best_move = ai.find_best_move(board, legal_moves, turn)

            print("\nBest move:", best_move)


    finally:

        engine.terminate()
        engine.wait()




    def minimax_without_pruning(

        self,
        board,
        legal_moves,
        depth,
        maximizing_player,
        status="NORMAL"

    ):

        self.nodes_searched += 1


        # Terminal positions
        if status == "CHECKMATE":

            return -100000 if maximizing_player else 100000


        if status in ("STALEMATE", "DRAW_INSUFFICIENT_MATERIAL"):

            return 0


        # Leaf node evaluation
        if depth == 0:

            return evaluate_board(board)


        if not legal_moves:

            return evaluate_board(board)



        # Maximizing player: White
        if maximizing_player:

            best_score = float('-inf')


            for move in legal_moves:

                response = send_move_to_engine(self.engine, move)


                if response != "MOVE_OK":

                    raise RuntimeError(
                        f"Engine rejected legal move {move}: {response}"
                    )


                try:

                    new_board, next_moves, next_status, next_turn = (
                        get_position(self.engine)
                    )


                    score = self.minimax_without_pruning(

                        new_board,
                        next_moves,
                        depth - 1,
                        maximizing_player=(next_turn == "WHITE"),
                        status=next_status

                    )


                finally:

                    self.undo_move()


                best_score = max(best_score, score)


            return best_score



        # Minimizing player: Black
        else:

            best_score = float('inf')


            for move in legal_moves:

                response = send_move_to_engine(self.engine, move)


                if response != "MOVE_OK":

                    raise RuntimeError(
                        f"Engine rejected legal move {move}: {response}"
                    )


                try:

                    new_board, next_moves, next_status, next_turn = (
                        get_position(self.engine)
                    )


                    score = self.minimax_without_pruning(

                        new_board,
                        next_moves,
                        depth - 1,
                        maximizing_player=(next_turn == "WHITE"),
                        status=next_status

                    )


                finally:

                    self.undo_move()


                best_score = min(best_score, score)


            return best_score
