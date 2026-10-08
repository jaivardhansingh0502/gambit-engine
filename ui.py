import tkinter as tk
import subprocess
import threading


class GambitUI:

    def __init__(self, root):



        self.root = root
        self.root.title("Gambit Chess")
        self.root.minsize(700, 600)




        self.engine = subprocess.Popen(
            ["gambit.exe"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )




        self.board = []
        self.legal_moves = []




        self.selected_square = None
        self.selected_moves = []




        self.last_move = None
        self.white_turn = True


        self.move_history = []

        self.game_status = "NORMAL"
        self.engine_busy = False



        self.main_frame = tk.Frame(self.root)



        self.main_frame.pack(
            fill="both",
            expand=True
        )




        self.canvas = tk.Canvas(
            self.main_frame,
            highlightthickness=0
        )




        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )





        self.history_frame = tk.Frame(
            self.main_frame,
            width=260
        )




        self.history_frame.pack(
            side="right",
            fill="y"
        )




        self.history_frame.pack_propagate(False)




        self.history_title = tk.Label(
            self.history_frame,
            text="Move History",
            font=("Arial", 18, "bold")
        )




        self.history_title.pack(
            pady=15
        )




        self.history_list = tk.Listbox(
            self.history_frame,
            font=("Consolas", 13),
            borderwidth=0,
            highlightthickness=0
        )




        self.history_list.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )




        self.new_game_button = tk.Button(
        self.history_frame,
        text="New Game",
        font=("Arial", 13, "bold"),
        command=self.new_game
    )



        self.new_game_button.pack(
            fill="x",
            padx=10,
            pady=10
        )


        self.canvas.bind(
                "<Configure>",
                self.on_resize
            )




        self.canvas.bind(
            "<Button-1>",
            self.on_click
        )




        self.root.after(
            100,
            self.start_engine_read
        )




        self.root.state("zoomed")




    def start_engine_read(self):

        threading.Thread(
            target=self.get_position,
            daemon=True
        ).start()





    def get_position(self):



        self.engine.stdin.write("GET_MOVES\n")
        self.engine.stdin.flush()



        board = []
        legal_moves = []
        status = "NORMAL"



        section = None




        while True:



            line = self.engine.stdout.readline().strip()




            if not line:
                continue



            if line == "BOARD":
                section = "board"
                continue



            if line == "MOVES":
                section = "moves"
                continue


            if line == "STATUS":
                section = "status"
                continue


            if line == "END":
                break



            if section == "board":
                board.append(list(line))



            elif section == "moves":
                legal_moves.append(line)



            elif section == "status":
                self.game_status = line



        self.board = board
        self.legal_moves = legal_moves
        self.engine_busy = False



        self.root.after(
            0,
            self.draw_board
        )



    def on_resize(self, event):

        if self.board:
            self.draw_board()



    def on_click(self, event):



        if self.engine_busy:
            return



        if not self.board:
            return



        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()



        board_size = min(width, height - 40)



        square_size = board_size / 8



        offset_x = (width - board_size) / 2
        offset_y = 20 + (height - 40 - board_size) / 2




        col = int((event.x - offset_x) / square_size)
        row = int((event.y - offset_y) / square_size)



        if row < 0 or row >= 8 or col < 0 or col >= 8:
            return



        clicked_square = self.square_to_notation(row, col)



        if self.selected_square is None:



            piece = self.board[row][col]



            if piece == ".":
                return



            moves = []



            for move in self.legal_moves:


                if move[:2] == clicked_square:
                    moves.append(move)



            if not moves:
                return


            self.selected_square = clicked_square
            self.selected_moves = moves


            self.draw_board()



        else:

            move_found = None

            for move in self.selected_moves:

                if move[2:4] == clicked_square:
                    move_found = move
                    break



            if move_found is not None:

                self.selected_square = None
                self.selected_moves = []

                self.last_move = move_found

                self.make_move(move_found)



            else:

                piece = self.board[row][col]

                if piece != ".":

                    moves = []

                    for move in self.legal_moves:

                        if move[:2] == clicked_square:
                            moves.append(move)

                    if moves:

                        self.selected_square = clicked_square
                        self.selected_moves = moves

                    else:

                        self.selected_square = None
                        self.selected_moves = []



                else:

                    self.selected_square = None
                    self.selected_moves = []

                self.draw_board()




    def make_move(self, move):



        self.engine_busy = True

        threading.Thread(
            target=self.send_move,
            args=(move,),
            daemon=True
        ).start()




    def send_move(self, move):



        self.engine.stdin.write(
            f"MAKE_MOVE {move}\n"
        )



        self.engine.stdin.flush()



        response = self.engine.stdout.readline().strip()



        if response != "MOVE_OK":



            self.engine_busy = False



            self.root.after(
                0,
                self.draw_board
            )

            return



        self.move_history.append(move)



        self.white_turn = not self.white_turn



        self.root.after(
            0,
            self.update_move_history
        )



        self.get_position()


    def new_game(self):



        if self.engine_busy:
            return




        self.engine_busy = True




        self.new_game_button.config(
            state="disabled"
        )




        threading.Thread(
            target=self.send_new_game,
            daemon=True
        ).start()






    def send_new_game(self):



        self.engine.stdin.write(
            "NEW_GAME\n"
        )



        self.engine.stdin.flush()



        response = self.engine.stdout.readline().strip()



        if response != "NEW_GAME_OK":



            self.engine_busy = False



            self.root.after(
                0,
                lambda: self.new_game_button.config(
                    state="normal"
                )
            )



            return

        

        self.board = []
        self.legal_moves = []
        


        self.selected_square = None
        self.selected_moves = []



        self.last_move = None



        self.white_turn = True
        self.move_history = []
        self.game_status = "NORMAL"


        self.root.after(
            0,
            self.update_move_history
        )



        self.root.after(
            0,
            self.start_engine_read
        )


    def update_move_history(self):



        self.history_list.delete(
            0,
            tk.END
        )




        for i in range(0, len(self.move_history), 2):



            move_number = (i // 2) + 1



            white_move = self.move_history[i]



            if i + 1 < len(self.move_history):
                black_move = self.move_history[i + 1]




                text = (
                    f"{move_number}. "
                    f"{white_move}    "
                    f"{black_move}"
                )




            else:
                text = (
                    f"{move_number}. "
                    f"{white_move}"
                )




            self.history_list.insert(
                tk.END,
                text
            )





    def square_to_notation(self, row, col):



        file = chr(ord("a") + col)
        rank = str(8 - row)

        return file + rank




    def draw_board(self):



        if not self.board:
            return




        self.canvas.delete("all")




        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()




        # Turn / Game Status
        if self.game_status == "CHECK":
            turn_text = (
                "White to move — CHECK"
                if self.white_turn
                else "Black to move — CHECK"
            )




        elif self.game_status == "CHECKMATE":
            turn_text = (
                "CHECKMATE — Black wins"
                if self.white_turn
                else "CHECKMATE — White wins"
            )




        elif self.game_status == "STALEMATE":
            turn_text = "STALEMATE"




        else:
            turn_text = (
                "White to move"
                if self.white_turn
                else "Black to move"
            )




        self.canvas.create_text(
            width / 2,
            10,
            text=turn_text,
            font=("Arial", 16, "bold")
        )



        board_size = min(width, height - 40)




        square_size = board_size / 8




        offset_x = (width - board_size) / 2
        offset_y = 20 + (height - 40 - board_size) / 2




        light = "#F0D9B5"
        dark = "#B58863"




        selected_color = "#F6F669"
        move_color = "#8FBC8F"
        last_move_color = "#D9A441"




        for row in range(8):

            for col in range(8):





                x1 = offset_x + col * square_size
                y1 = offset_y + row * square_size




                x2 = x1 + square_size
                y2 = y1 + square_size

                color = (
                    light
                    if (row + col) % 2 == 0
                    else dark
                )





                square = self.square_to_notation(row, col)





                # Last move highlighting
                if self.last_move is not None:

                    if (
                        square == self.last_move[:2]
                        or square == self.last_move[2:4]
                    ):
                        color = last_move_color




                # Selected square
                if square == self.selected_square:

                    color = selected_color




                # Legal move highlighting
                elif square in [
                    move[2:4]
                    for move in self.selected_moves
                ]:


                    

                    color = move_color




                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=color,
                    outline=""
                )




                piece = self.board[row][col]




                if piece != ".":

                    self.draw_piece(
                        piece,
                        x1 + square_size / 2,
                        y1 + square_size / 2,
                        square_size
                    )




                # Rank numbers
                if col == 0:



                    self.canvas.create_text(
                        x1 + 8,
                        y1 + 8,
                        text=str(8 - row),
                        anchor="nw",
                        font=("Arial", 11, "bold"),
                        fill=dark if (row + col) % 2 == 0 else light
                    )




                # File letters
                if row == 7:




                    self.canvas.create_text(
                        x2 - 8,
                        y2 - 8,
                        text=chr(ord("a") + col),
                        anchor="se",
                        font=("Arial", 11, "bold"),
                        fill=dark if (row + col) % 2 == 0 else light
                    )



    def draw_piece(self, piece, x, y, square_size):

        pieces = {
            "K": "♔",
            "Q": "♕",
            "R": "♖",
            "B": "♗",
            "N": "♘",
            "P": "♙",
            "k": "♚",
            "q": "♛",
            "r": "♜",
            "b": "♝",
            "n": "♞",
            "p": "♟"
        }

        symbol = pieces.get(piece, "")

        font_size = max(
            20,
            int(square_size * 0.68)
        )



        self.canvas.create_text(
            x,
            y,
            text=symbol,
            font=("Segoe UI Symbol", font_size)
        )


if __name__ == "__main__":

    root = tk.Tk()

    app = GambitUI(root)

    root.mainloop()