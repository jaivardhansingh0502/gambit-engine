import tkinter as tk
import subprocess
import threading


class GambitUI:

    def __init__(self, root):

        self.root = root
        self.root.title("Gambit Chess")
        self.root.minsize(600, 600)

        self.engine = subprocess.Popen(
            ["gambit.exe"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )

        self.board = []
        self.legal_moves = []

        self.canvas = tk.Canvas(
            self.root,
            highlightthickness=0
        )

        self.canvas.pack(
            fill="both",
            expand=True
        )

        self.canvas.bind(
            "<Configure>",
            self.on_resize
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

            if line == "END":
                break

            if section == "board":
                board.append(list(line))

            elif section == "moves":
                legal_moves.append(line)

        self.board = board
        self.legal_moves = legal_moves

        self.root.after(
            0,
            self.draw_board
        )

    def on_resize(self, event):

        if self.board:
            self.draw_board()

    def draw_board(self):

        if not self.board:
            return

        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        board_size = min(width, height)

        square_size = board_size / 8

        offset_x = (width - board_size) / 2
        offset_y = (height - board_size) / 2

        light = "#F0D9B5"
        dark = "#B58863"

        for row in range(8):

            for col in range(8):

                x1 = offset_x + col * square_size
                y1 = offset_y + row * square_size

                x2 = x1 + square_size
                y2 = y1 + square_size

                if (row + col) % 2 == 0:
                    color = light
                else:
                    color = dark

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