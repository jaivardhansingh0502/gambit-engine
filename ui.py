
import tkinter as tk
import subprocess
import threading
from tkinter import messagebox

from ai import AI, get_position, send_move_to_engine


GAME_OVER_STATUSES = (
    "CHECKMATE",
    "STALEMATE",
    "DRAW_INSUFFICIENT_MATERIAL",
)

AI_DIFFICULTY_DEPTHS = {
    "Easy (Depth 1)": 1,
    "Medium (Depth 2)": 2,
    "Hard (Depth 3)": 3,
}


def square_to_notation(row, col):
    file_char = chr(ord("a") + col)
    rank_char = str(8 - row)
    return file_char + rank_char


def find_king_square(board, white_turn):
    target = "K" if white_turn else "k"
    for row in range(len(board)):
        for col in range(len(board[row])):
            if board[row][col] == target:
                return square_to_notation(row, col)
    return None


def get_promotion_map(moves):
    return {
        move[4].lower(): move
        for move in moves
        if len(move) >= 5 and move[4].lower() in "qrbn"
    }


def format_status_text(game_status, white_turn, engine_busy):
    if not white_turn and engine_busy:
        return "Black — AI thinking...", "#1D4ED8"

    if game_status == "CHECK":
        text = (
            "White to move — CHECK"
            if white_turn
            else "Black to move — CHECK"
        )
        return text, "#B91C1C"

    if game_status == "CHECKMATE":
        text = (
            "CHECKMATE — Black wins"
            if white_turn
            else "CHECKMATE — White wins"
        )
        return text, "#B91C1C"

    if game_status == "STALEMATE":
        return "STALEMATE — Draw", "#B45309"

    if game_status == "DRAW_INSUFFICIENT_MATERIAL":
        return "DRAW — Insufficient Material", "#B45309"

    text = "White to move" if white_turn else "Black to move"
    return text, "#111827"


def get_board_geometry(width, height, top_margin=44):
    available_height = max(80, height - top_margin - 12)
    board_size = max(80, min(width - 16, available_height))
    square_size = board_size / 8
    offset_x = (width - board_size) / 2
    offset_y = top_margin + (available_height - board_size) / 2
    return board_size, square_size, offset_x, offset_y


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
            encoding="utf-8",
            bufsize=1
        )

        self.ai = AI(self.engine)

        self.board = []
        self.legal_moves = []
        self.selected_square = None
        self.selected_moves = []
        self.last_move = None
        self.white_turn = True
        self.move_history = []
        self.game_status = "NORMAL"
        self.engine_busy = True
        self.closing = False
        self.engine_lock = threading.Lock()

        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            self.main_frame,
            highlightthickness=0
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        self.history_frame = tk.Frame(
            self.main_frame,
            width=260
        )
        self.history_frame.pack(side="right", fill="y")
        self.history_frame.pack_propagate(False)

        self.history_title = tk.Label(
            self.history_frame,
            text="Move History",
            font=("Arial", 18, "bold")
        )
        self.history_title.pack(pady=15)

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

        self.difficulty_frame = tk.Frame(self.history_frame)
        self.difficulty_frame.pack(fill="x", padx=10, pady=(0, 8))

        tk.Label(
            self.difficulty_frame,
            text="AI Level:",
            font=("Arial", 11, "bold")
        ).pack(side="left")

        self.difficulty_var = tk.StringVar(value="Medium (Depth 2)")
        self.difficulty_menu = tk.OptionMenu(
            self.difficulty_frame,
            self.difficulty_var,
            *AI_DIFFICULTY_DEPTHS.keys()
        )
        self.difficulty_menu.config(font=("Arial", 11))
        self.difficulty_menu.pack(side="right", fill="x", expand=True, padx=(8, 0))

        self.undo_button = tk.Button(
            self.history_frame,
            text="Undo Move",
            font=("Arial", 13, "bold"),
            command=self.undo_last_turn,
            state="disabled"
        )
        self.undo_button.pack(
            fill="x",
            padx=10,
            pady=(0, 6)
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
            pady=(0, 10)
        )

        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Button-1>", self.on_click)

        self.root.state("zoomed")

        self.root.after(100, self.initial_position)

    # ---------------- ENGINE POSITION ----------------

    def initial_position(self):
        threading.Thread(
            target=self.load_initial_position,
            daemon=True
        ).start()

    def load_initial_position(self):
        try:
            with self.engine_lock:
                board, moves, status, turn = get_position(self.engine)

            if not self.closing:
                self.root.after(
                    0,
                    lambda: self.update_position(
                        board, moves, status, turn
                    )
                )

        except Exception as e:
            if not self.closing:
                self.root.after(
                    0,
                    lambda err=str(e): messagebox.showerror(
                        "Engine Error", err
                    )
                )

    def get_ai_depth(self):
        return AI_DIFFICULTY_DEPTHS.get(self.difficulty_var.get(), 2)

    def _update_controls(self):
        if self.closing:
            return
        state = "disabled" if self.engine_busy else "normal"
        self.new_game_button.config(state=state)
        self.difficulty_menu.config(state=state)
        can_undo = (not self.engine_busy) and len(self.move_history) > 0
        self.undo_button.config(
            state="normal" if can_undo else "disabled"
        )

    def update_position(
        self,
        board,
        moves,
        status,
        turn,
        last_move=None,
        appended_move=None,
        keep_busy=False
    ):
        if self.closing:
            return

        self.board = board
        self.legal_moves = moves
        self.game_status = status
        self.white_turn = turn == "WHITE"
        if last_move is not None:
            self.last_move = last_move
        if appended_move is not None:
            self.move_history.append(appended_move)
            self.update_move_history()
        self.engine_busy = keep_busy

        self._update_controls()
        self.draw_board()

    # ---------------- MOVE SELECTION ----------------

    def on_click(self, event):

        if self.engine_busy:
            return

        if self.game_status in GAME_OVER_STATUSES:
            return

        if not self.white_turn:
            return

        if not self.board:
            return

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        _, square_size, offset_x, offset_y = get_board_geometry(width, height)

        col = int((event.x - offset_x) / square_size)
        row = int((event.y - offset_y) / square_size)

        if row < 0 or row >= 8 or col < 0 or col >= 8:
            return

        clicked_square = self.square_to_notation(row, col)

        if self.selected_square is None:

            piece = self.board[row][col]

            if piece == "." or piece.islower():
                return

            moves = [
                move for move in self.legal_moves
                if move[:2] == clicked_square
            ]

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

                same_destination = [
                    move for move in self.selected_moves
                    if move[2:4] == clicked_square
                ]

                if any(len(move) >= 5 for move in same_destination):

                    move_found = self.choose_promotion(
                        same_destination
                    )

                    if move_found is None:
                        return

                self.selected_square = None
                self.selected_moves = []

                self.make_move(move_found)

            else:

                piece = self.board[row][col]

                if piece != "." and piece.isupper():

                    moves = [
                        move for move in self.legal_moves
                        if move[:2] == clicked_square
                    ]

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

    # ---------------- PROMOTION ----------------

    def choose_promotion(self, moves):
        promotion_moves = get_promotion_map(moves)

        if not promotion_moves:
            return moves[0] if moves else None

        dialog = tk.Toplevel(self.root)
        dialog.title("Pawn Promotion")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        selected_move = {"value": None}

        tk.Label(
            dialog,
            text="Choose promotion piece:",
            font=("Arial", 12, "bold"),
            padx=16,
            pady=10
        ).pack()

        button_frame = tk.Frame(dialog, padx=12, pady=10)
        button_frame.pack()

        labels = [
            ("q", "♕ Queen"),
            ("r", "♖ Rook"),
            ("b", "♗ Bishop"),
            ("n", "♘ Knight"),
        ]

        def select_piece(key):
            selected_move["value"] = promotion_moves.get(key)
            dialog.destroy()

        for key, label in labels:
            if key in promotion_moves:
                tk.Button(
                    button_frame,
                    text=label,
                    font=("Segoe UI Symbol", 12),
                    width=10,
                    command=lambda k=key: select_piece(k)
                ).pack(side="left", padx=4)

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{max(0, x)}+{max(0, y)}")

        self.root.wait_window(dialog)
        return selected_move["value"]

    # ---------------- HUMAN MOVE ----------------

    def make_move(self, move):

        if self.engine_busy:
            return

        self.engine_busy = True
        self._update_controls()
        self.draw_board()

        threading.Thread(
            target=self.process_human_move,
            args=(move,),
            daemon=True
        ).start()

    def process_human_move(self, move):

        try:
            with self.engine_lock:
                response = send_move_to_engine(
                    self.engine, move
                )

                if response != "MOVE_OK":
                    raise RuntimeError(
                        f"Human move rejected: {response}"
                    )

                board, moves, status, turn = get_position(
                    self.engine
                )

            game_over = status in (
                "CHECKMATE",
                "STALEMATE",
                "DRAW_INSUFFICIENT_MATERIAL"
            )
            should_ai_move = (not game_over) and (turn == "BLACK")

            if not self.closing:
                self.root.after(
                    0,
                    lambda: self.update_position(
                        board,
                        moves,
                        status,
                        turn,
                        last_move=move,
                        appended_move=move,
                        keep_busy=should_ai_move
                    )
                )

            if should_ai_move and not self.closing:
                self.process_ai_turn(board, moves, status, turn)

        except Exception as e:
            if not self.closing:
                self.root.after(
                    0,
                    lambda err=str(e): self._handle_move_error("Move Error", err)
                )

    def _handle_move_error(self, title, err):
        if not self.closing:
            messagebox.showerror(title, err)
            self.engine_busy = False
            self._update_controls()
            self.draw_board()

    # ---------------- AI MOVE ----------------

    def process_ai_turn(self, board, moves, status, turn):

        try:
            if status in GAME_OVER_STATUSES:
                if not self.closing:
                    self.root.after(
                        0,
                        lambda: self.update_position(
                            board, moves, status, turn
                        )
                    )
                return

            depth = self.get_ai_depth()

            with self.engine_lock:
                ai_move = self.ai.find_best_move(
                    board,
                    moves,
                    turn,
                    depth=depth
                )

                if ai_move is None:
                    if not self.closing:
                        self.root.after(
                            0,
                            lambda: setattr(self, "engine_busy", False)
                        )
                    return

                response = send_move_to_engine(
                    self.engine, ai_move
                )

                if response != "MOVE_OK":
                    raise RuntimeError(
                        f"AI move rejected: {response}"
                    )

                board, moves, status, turn = get_position(
                    self.engine
                )

            if not self.closing:
                self.root.after(
                    0,
                    lambda: self.update_position(
                        board,
                        moves,
                        status,
                        turn,
                        last_move=ai_move,
                        appended_move=ai_move,
                        keep_busy=False
                    )
                )

        except Exception as e:
            if not self.closing:
                self.root.after(
                    0,
                    lambda err=str(e): self._handle_move_error("AI Error", err)
                )

    # ---------------- UNDO & NEW GAME ----------------

    def undo_last_turn(self):
        if self.engine_busy or not self.move_history:
            return

        undo_count = 1 if len(self.move_history) % 2 == 1 else 2
        self.engine_busy = True
        self._update_controls()

        threading.Thread(
            target=self._process_undo,
            args=(undo_count,),
            daemon=True
        ).start()

    def _process_undo(self, undo_count):
        try:
            with self.engine_lock:
                for _ in range(undo_count):
                    self.engine.stdin.write("UNDO_MOVE\n")
                    self.engine.stdin.flush()
                    response = self.engine.stdout.readline().strip()
                    if response != "UNDO_OK":
                        raise RuntimeError(f"Undo failed: {response}")

                board, moves, status, turn = get_position(self.engine)

            if not self.closing:
                self.root.after(
                    0,
                    lambda: self._apply_undo_state(
                        undo_count, board, moves, status, turn
                    )
                )

        except Exception as e:
            if not self.closing:
                self.root.after(
                    0,
                    lambda err=str(e): self._handle_move_error("Undo Error", err)
                )

    def _apply_undo_state(self, undo_count, board, moves, status, turn):
        if self.closing:
            return

        for _ in range(undo_count):
            if self.move_history:
                self.move_history.pop()

        self.selected_square = None
        self.selected_moves = []
        self.last_move = self.move_history[-1] if self.move_history else None
        self.update_move_history()
        self.update_position(board, moves, status, turn)

    def new_game(self):

        if self.engine_busy:
            return

        self.engine_busy = True
        self._update_controls()

        threading.Thread(
            target=self.send_new_game,
            daemon=True
        ).start()

    def send_new_game(self):

        try:
            with self.engine_lock:
                self.engine.stdin.write(
                    "NEW_GAME\n"
                )
                self.engine.stdin.flush()

                response = self.engine.stdout.readline().strip()

                if response != "NEW_GAME_OK":
                    raise RuntimeError(
                        f"New game failed: {response}"
                    )

                board, moves, status, turn = get_position(
                    self.engine
                )

            if not self.closing:
                self.root.after(
                    0,
                    lambda: self._apply_new_game_state(
                        board, moves, status, turn
                    )
                )

        except Exception as e:
            if not self.closing:
                self.root.after(
                    0,
                    lambda err=str(e): self._handle_move_error("New Game Error", err)
                )

    def _apply_new_game_state(self, board, moves, status, turn):
        if self.closing:
            return

        self.selected_square = None
        self.selected_moves = []
        self.last_move = None
        self.move_history = []
        self.update_move_history()
        self.update_position(board, moves, status, turn)

    # ---------------- MOVE HISTORY ----------------

    def update_move_history(self):

        self.history_list.delete(
            0, tk.END
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
                tk.END, text
            )

    # ---------------- BOARD DRAWING ----------------

    def square_to_notation(self, row, col):
        return square_to_notation(row, col)

    def on_resize(self, event):

        if self.board:
            self.draw_board()

    def draw_board(self):

        if not self.board:
            return

        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        turn_text, status_color = format_status_text(
            self.game_status,
            self.white_turn,
            self.engine_busy
        )

        self.canvas.create_text(
            width / 2,
            22,
            text=turn_text,
            font=("Arial", 16, "bold"),
            fill=status_color
        )

        _, square_size, offset_x, offset_y = get_board_geometry(width, height)

        light = "#F0D9B5"
        dark = "#B58863"
        selected_color = "#F6F669"
        move_color = "#8FBC8F"
        last_move_color = "#D9A441"
        check_color = "#E06C75"

        king_in_check_square = (
            find_king_square(self.board, self.white_turn)
            if self.game_status in ("CHECK", "CHECKMATE")
            else None
        )

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

                square = self.square_to_notation(
                    row, col
                )

                if self.last_move is not None:

                    if (
                        square == self.last_move[:2]
                        or square == self.last_move[2:4]
                    ):
                        color = last_move_color

                if square == king_in_check_square:
                    color = check_color

                if square == self.selected_square:
                    color = selected_color

                elif square in [
                    move[2:4]
                    for move in self.selected_moves
                ]:
                    color = move_color

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline=""
                )

                piece = self.board[row][col]

                if piece != "." and piece != " ":

                    self.draw_piece(
                        piece,
                        x1 + square_size / 2,
                        y1 + square_size / 2,
                        square_size
                    )

                if col == 0:

                    self.canvas.create_text(
                        x1 + 8,
                        y1 + 8,
                        text=str(8 - row),
                        anchor="nw",
                        font=("Arial", 11, "bold"),
                        fill=dark if (row + col) % 2 == 0 else light
                    )

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

    # ---------------- SHUTDOWN ----------------

    def close(self):
        self.closing = True

        try:
            if self.engine.poll() is None:
                self.engine.terminate()
                self.engine.wait(timeout=2)
            if self.engine.stdin:
                self.engine.stdin.close()
            if self.engine.stdout:
                self.engine.stdout.close()

        except Exception:
            pass

        self.root.destroy()


if __name__ == "__main__":

    root = tk.Tk()
    app = GambitUI(root)

    root.protocol(
        "WM_DELETE_WINDOW",
        app.close
    )

    root.mainloop()
