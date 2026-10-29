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



    
    
    
    def order_moves(self, board, legal_moves):



        piece_values = {
            'p': 1,
            'n': 3,
            'b': 3,
            'r': 5,
            'q': 9,
            'k': 100
        }



        def move_score(move):



            start_row = 8 - int(move[1])
            start_col = ord(move[0]) - ord('a')



            end_row = 8 - int(move[3])
            end_col = ord(move[2]) - ord('a')



            attacker = board[start_row][start_col].lower()
            victim = board[end_row][end_col].lower()

           

            score = 0



            # Captures: valuable victim, cheaper attacker
            if victim in piece_values:




                score += 10 * piece_values[victim]
                score -= piece_values[attacker]





            # Promotions
            if len(move) == 5:



                promoted_piece = move[4].lower()

                score += piece_values.get(promoted_piece, 0) * 10




            return score


        


        return sorted(
            legal_moves,
            key=move_score,
            reverse=True
        )





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
            return self.quiescence_search(
                board,
                legal_moves,
                maximizing_player,
                alpha,
                beta,
                status
            )


        if not legal_moves:

            return evaluate_board(board)




        # Maximizing player: White
        if maximizing_player:

            best_score = float('-inf')


            for move in self.order_moves(board, legal_moves):


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


            for move in self.order_moves(board, legal_moves):


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





    
    def quiescence_search(
    self,
    board,
    legal_moves,
    maximizing_player,
    alpha=float('-inf'),
    beta=float('inf'),
    status="NORMAL",
    remaining_depth=4
):
        self.nodes_searched += 1






        # Terminal positions
        if status == "CHECKMATE":
            return -100000 if maximizing_player else 100000





        if status in ("STALEMATE", "DRAW_INSUFFICIENT_MATERIAL"):
            return 0





        in_check = status == "CHECK"
        stand_pat = evaluate_board(board)





        # At the depth limit, return static evaluation unless in check.
        if remaining_depth <= 0 and not in_check:
            return stand_pat





        # Stand-pat is allowed only when the king is not in check.
        if not in_check:
            if maximizing_player:
                if stand_pat >= beta:
                    return stand_pat




                
                alpha = max(alpha, stand_pat)







            else:
                if stand_pat <= alpha:
                    return stand_pat


                
                beta = min(beta, stand_pat)






            best_score = stand_pat







        else:
            # In check, a legal evasion must be played.
            best_score = (
                float('-inf') if maximizing_player else float('inf')
            )






        # In check: examine every legal evasion.
        # Otherwise: examine captures and promotions only.
        tactical_moves = []





        for move in legal_moves:
            start_row = 8 - int(move[1])
            start_col = ord(move[0]) - ord('a')
            end_row = 8 - int(move[3])
            end_col = ord(move[2]) - ord('a')





            attacker = board[start_row][start_col]
            victim = board[end_row][end_col]




            is_capture = victim not in ('.', ' ')



            # En passant capture
            if (
                attacker.lower() == 'p'
                and start_col != end_col
                and not is_capture
            ):


                
                is_capture = True

            is_promotion = len(move) == 5




            if in_check or is_capture or is_promotion:
                tactical_moves.append(move)





        for move in self.order_moves(board, tactical_moves):
            response = send_move_to_engine(self.engine, move)




            if response != "MOVE_OK":
                raise RuntimeError(
                    f"Engine rejected legal move {move}: {response}"
                )


            

            try:
                (
                    new_board,
                    next_moves,
                    next_status,
                    next_turn
                ) = get_position(self.engine)




                next_maximizing = next_turn == "WHITE"

                # At the depth limit, still allow one legal evasion
                # if the current side is in check, then stop recursing.





                if in_check and remaining_depth <= 0:
                    if next_status == "CHECKMATE":
                        score = (
                            -100000 if next_maximizing else 100000
                        )







                    elif next_status in (
                        "STALEMATE",
                        "DRAW_INSUFFICIENT_MATERIAL"
                    ):




                        
                        score = 0
                    else:
                        score = evaluate_board(new_board)






                else:
                    score = self.quiescence_search(
                        new_board,
                        next_moves,
                        maximizing_player=next_maximizing,
                        alpha=alpha,
                        beta=beta,
                        status=next_status,
                        remaining_depth=remaining_depth - 1
                    )







            finally:
                self.undo_move()





            if maximizing_player:
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)




            else:
                best_score = min(best_score, score)
                beta = min(beta, best_score)





            if alpha >= beta:
                break



            

        return best_score


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
    
    
    
    
    
        


    def compare_searches(self, board, legal_moves, turn, depth=2):
    
            import time
    
    
            results = {}
    
    
            # Run both algorithms from the same root position
            for algorithm in ("Minimax", "Alpha-Beta"):
    
                self.nodes_searched = 0
    
                best_move = None
    
                best_score = (
                    float('-inf') if turn == "WHITE"
                    else float('inf')
                )
    
                alpha = float('-inf')
    
                beta = float('inf')
    
    
                start_time = time.perf_counter()
    
    
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
    
    
                        if algorithm == "Minimax":
    
                            score = self.minimax_without_pruning(
    
                                new_board,
                                next_moves,
                                depth,
                                maximizing_player=(next_turn == "WHITE"),
                                status=next_status
    
                            )
    
                        else:
    
                            score = self.minimax(
    
                                new_board,
                                next_moves,
                                depth,
                                maximizing_player=(next_turn == "WHITE"),
                                alpha=alpha,
                                beta=beta,
                                status=next_status
    
                            )
    
                    finally:
    
                        self.undo_move()
    
    
                    if turn == "WHITE":
    
                        if score > best_score:
    
                            best_score = score
    
                            best_move = move
    
                        if algorithm == "Alpha-Beta":
    
                            alpha = max(alpha, best_score)
    
                    else:
    
                        if score < best_score:
    
                            best_score = score
    
                            best_move = move
    
                        if algorithm == "Alpha-Beta":
    
                            beta = min(beta, best_score)
    
    
                elapsed = time.perf_counter() - start_time
    
    
                results[algorithm] = {
    
                    "best_move": best_move,
    
                    "best_score": best_score,
    
                    "nodes": self.nodes_searched,
    
                    "time": elapsed
    
                }
    
    
            print("\n===== SEARCH COMPARISON =====")
    
    
            for algorithm, result in results.items():
    
                print(f"\n{algorithm}")
    
                print(f"Best move: {result['best_move']}")
    
                print(f"Best score: {result['best_score']}")
    
                print(f"Nodes searched: {result['nodes']}")
    
                print(f"Time: {result['time']:.4f} seconds")
    
    
            print("\n===== IMPROVEMENT =====")
    
    
            minimax_nodes = results["Minimax"]["nodes"]
    
            alpha_beta_nodes = results["Alpha-Beta"]["nodes"]
    
    
            if minimax_nodes > 0:
    
                reduction = (
                    (minimax_nodes - alpha_beta_nodes)
                    / minimax_nodes
                ) * 100
    
                print(f"Node reduction: {reduction:.2f}%")
    
    
            return results





def play_test_moves(engine, moves):

    for move in moves:

        response = send_move_to_engine(engine, move)

        if response != "MOVE_OK":

            raise RuntimeError(
                f"Test move failed: {move} -> {response}"
            )

    return get_position(engine)





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


        # board, legal_moves, status, turn = get_position(engine)


        test_moves = ["e2e4", "d7d5", "e4d5", "d8d5", "b1c3"]

        board, legal_moves, status, turn = play_test_moves(engine, test_moves)




        
        




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

            ai.compare_searches(board, legal_moves, turn, depth=2)


    finally:

        engine.terminate()
        engine.wait()




    