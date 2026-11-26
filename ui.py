
import tkinter as tk
import subprocess
import threading
from tkinter import messagebox

from ai import AI, get_engine_evaluation, get_position, send_move_to_engine
from evaluation import (
    analyze_material,
    evaluate_board,
    format_evaluation_summary,
)


GAME_OVER_STATUSES = (
    "CHECKMATE",
    "STALEMATE",
    "DRAW_INSUFFICIENT_MATERIAL",
    "RESIGNED_WHITE",
    "RESIGNED_BLACK",
)

MODE_PVP = "PvP"
MODE_PVAI = "PvAI"

GAME_MODE_LABELS = {
    MODE_PVP: "Player vs Player (PvP)",
    MODE_PVAI: "Player vs AI (PvAI)",
}

AI_DIFFICULTY_DEPTHS = {
    "Easy (Depth 1)": 1,
    "Medium (Depth 3)": 3,
    "Hard (Depth 4)": 4,
}

AI_DIFFICULTY_TIME_LIMITS = {
    "Easy (Depth 1)": 0.5,
    "Medium (Depth 3)": 2.0,
    "Hard (Depth 4)": 4.5,
}

THEME = {
    "bg": "#181A20",
    "sidebar": "#20232C",
    "card": "#282C37",
    "border": "#363B4A",
    "text": "#F3F4F6",
    "muted": "#9CA3AF",
    "accent_blue": "#2563EB",
    "accent_green": "#059669",
    "accent_red": "#DC2626",
    "btn_bg": "#313644",
    "btn_active": "#3E4556",
    "list_bg": "#1B1E26",
}


def can_human_interact(game_mode, white_turn):
    return True if game_mode == MODE_PVP else white_turn


def is_own_piece(piece, white_turn):
    if piece in (".", " "):
        return False
    return piece.isupper() if white_turn else piece.islower()


def notation_to_coords(square):
    col = ord(square[0]) - ord("a")
    row = 8 - int(square[1])
    return row, col


def compute_advantage_ratio(score, max_pawns=10.0):
    clamped = max(-max_pawns, min(max_pawns, float(score)))
    return 0.5 + (clamped / max_pawns) * 0.45


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


def format_status_text(game_status, white_turn, engine_busy, game_mode=MODE_PVAI):
    if game_mode == MODE_PVAI and not white_turn and engine_busy:
        return "Black — AI thinking...", "#60A5FA"

    if game_status == "CHECK":
        text = (
            "White to move — CHECK"
            if white_turn
            else "Black to move — CHECK"
        )
        return text, "#F87171"

    if game_status == "CHECKMATE":
        text = (
            "CHECKMATE — Black wins"
            if white_turn
            else "CHECKMATE — White wins"
        )
        return text, "#F87171"

    if game_status == "STALEMATE":
        return "STALEMATE — Draw", "#FBBF24"

    if game_status == "DRAW_INSUFFICIENT_MATERIAL":
        return "DRAW — Insufficient Material", "#FBBF24"

    if game_status == "RESIGNED_WHITE":
        return "White resigned — Black wins", "#F87171"

    if game_status == "RESIGNED_BLACK":
        return "Black resigned — White wins", "#F87171"

    text = "White to move" if white_turn else "Black to move"
    return text, "#F3F4F6"


def get_board_geometry(width, height, top_margin=44):
    available_height = max(80, height - top_margin - 12)
    board_size = max(80, min(width - 16, available_height))
    square_size = board_size / 8
    offset_x = (width - board_size) / 2
    offset_y = top_margin + (available_height - board_size) / 2
    return board_size, square_size, offset_x, offset_y


class GambitUI:

    def __init__(self, root, game_mode=None, prompt_mode_on_start=True):
        self.root = root
        self.root.title("Gambit Chess")
        self.root.minsize(900, 680)
        self.root.configure(bg=THEME["bg"])

        self.engine = subprocess.Popen(
            ["gambit.exe"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1
        )

        self.ai = AI(self.engine)

        self.prompt_mode_on_start = prompt_mode_on_start
        self.game_mode = (
            game_mode if game_mode in GAME_MODE_LABELS else MODE_PVAI
        )
        self.engine_eval = 0

        self.board = []
        self.legal_moves = []
        self.selected_square = None
        self.selected_moves = []
        self.last_move = None
        self.white_turn = True
        self.move_history = []
        self.position_history = []
        self.view_index = -1
        self.animating = False
        self._anim_after_id = None
        self.game_status = "NORMAL"
        self.engine_busy = True
        self.closing = False
        self.engine_lock = threading.Lock()

        self.main_frame = tk.Frame(root, bg=THEME["bg"])
        self.main_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(
            self.main_frame,
            bg=THEME["bg"],
            highlightthickness=0
        )
        self.canvas.pack(side="left", fill="both", expand=True, padx=(10, 6), pady=8)

        self.history_frame = tk.Frame(
            self.main_frame,
            width=350,
            bg=THEME["sidebar"],
            highlightthickness=1,
            highlightbackground=THEME["border"]
        )
        self.history_frame.pack(side="right", fill="y", padx=(0, 10), pady=8)
        self.history_frame.pack_propagate(False)

        # ---- Header & Mode Selector ----
        self.header_frame = tk.Frame(self.history_frame, bg=THEME["sidebar"])
        self.header_frame.pack(fill="x", padx=12, pady=(12, 8))

        tk.Label(
            self.header_frame,
            text="♟ GAMBIT CHESS",
            font=("Segoe UI", 15, "bold"),
            fg=THEME["text"],
            bg=THEME["sidebar"],
            anchor="w"
        ).pack(fill="x")

        self.mode_label = tk.Label(
            self.header_frame,
            text=f"Mode: {GAME_MODE_LABELS[self.game_mode]}",
            font=("Segoe UI", 10, "bold"),
            fg="#93C5FD",
            bg=THEME["sidebar"],
            anchor="w"
        )
        self.mode_label.pack(fill="x", pady=(2, 6))

        self.mode_switch_frame = tk.Frame(self.header_frame, bg=THEME["sidebar"])
        self.mode_switch_frame.pack(fill="x")

        self.pvai_mode_btn = tk.Button(
            self.mode_switch_frame,
            text="Player vs AI",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            pady=6,
            cursor="hand2",
            command=lambda: self.select_mode_from_sidebar(MODE_PVAI)
        )
        self.pvai_mode_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.pvp_mode_btn = tk.Button(
            self.mode_switch_frame,
            text="Player vs Player",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            pady=6,
            cursor="hand2",
            command=lambda: self.select_mode_from_sidebar(MODE_PVP)
        )
        self.pvp_mode_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # ---- Evaluation Card ----
        self.eval_frame = tk.LabelFrame(
            self.history_frame,
            text=" Position Evaluation ",
            font=("Segoe UI", 10, "bold"),
            fg=THEME["muted"],
            bg=THEME["card"],
            bd=1,
            relief="solid",
            highlightbackground=THEME["border"],
            padx=10,
            pady=8
        )
        self.eval_frame.pack(fill="x", padx=12, pady=(0, 8))

        self.eval_headline_label = tk.Label(
            self.eval_frame,
            text="Position is equal: 0.0",
            font=("Segoe UI", 12, "bold"),
            fg=THEME["text"],
            bg=THEME["card"],
            anchor="w"
        )
        self.eval_headline_label.pack(fill="x")

        self.eval_bar = tk.Canvas(
            self.eval_frame,
            height=16,
            bg="#111827",
            highlightthickness=1,
            highlightbackground=THEME["border"]
        )
        self.eval_bar.pack(fill="x", pady=(6, 6))
        self.eval_bar.bind("<Configure>", lambda _e: self._draw_eval_bar(self.current_material_score))
        self.current_material_score = 0

        self.engine_eval_label = tk.Label(
            self.eval_frame,
            text="C++ Engine Eval (material-only): 0.0",
            font=("Segoe UI", 9),
            fg="#D1D5DB",
            bg=THEME["card"],
            anchor="w"
        )
        self.engine_eval_label.pack(fill="x")

        self.ai_eval_label = tk.Label(
            self.eval_frame,
            text="AI Positional Eval (Material + PST): 0.00",
            font=("Segoe UI", 9),
            fg="#D1D5DB",
            bg=THEME["card"],
            anchor="w"
        )
        self.ai_eval_label.pack(fill="x", pady=(0, 6))

        self.white_material_label = tk.Label(
            self.eval_frame,
            text="White: Q:1  R:2  B:2  N:2  P:8",
            font=("Consolas", 9),
            fg="#F9FAFB",
            bg=THEME["card"],
            anchor="w"
        )
        self.white_material_label.pack(fill="x")

        self.black_material_label = tk.Label(
            self.eval_frame,
            text="Black: q:1  r:2  b:2  n:2  p:8",
            font=("Consolas", 9),
            fg="#CBD5E1",
            bg=THEME["card"],
            anchor="w"
        )
        self.black_material_label.pack(fill="x")

        self.material_diff_label = tk.Label(
            self.eval_frame,
            text="Material is equal. (0.0 pts)",
            font=("Segoe UI", 9),
            fg="#93C5FD",
            bg=THEME["card"],
            anchor="w",
            justify="left",
            wraplength=300
        )
        self.material_diff_label.pack(fill="x", pady=(5, 0))

        # ---- Move History ----
        self.history_title = tk.Label(
            self.history_frame,
            text="Move History",
            font=("Segoe UI", 11, "bold"),
            fg=THEME["muted"],
            bg=THEME["sidebar"],
            anchor="w"
        )
        self.history_title.pack(fill="x", padx=12, pady=(2, 4))

        self.history_list_frame = tk.Frame(
            self.history_frame,
            bg=THEME["list_bg"],
            highlightthickness=1,
            highlightbackground=THEME["border"]
        )
        self.history_list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.history_scroll = tk.Scrollbar(self.history_list_frame)
        self.history_scroll.pack(side="right", fill="y")

        self.history_list = tk.Listbox(
            self.history_list_frame,
            font=("Consolas", 11),
            bg=THEME["list_bg"],
            fg=THEME["text"],
            selectbackground=THEME["accent_blue"],
            selectforeground="#FFFFFF",
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=self.history_scroll.set
        )
        self.history_list.pack(side="left", fill="both", expand=True, padx=6, pady=4)
        self.history_scroll.config(command=self.history_list.yview)

        # ---- Controls ----
        self.difficulty_frame = tk.Frame(self.history_frame, bg=THEME["sidebar"])
        self.difficulty_frame.pack(fill="x", padx=12, pady=(0, 8))

        tk.Label(
            self.difficulty_frame,
            text="AI Level:",
            font=("Segoe UI", 10, "bold"),
            fg=THEME["text"],
            bg=THEME["sidebar"]
        ).pack(side="left")

        self.difficulty_var = tk.StringVar(value="Medium (Depth 3)")
        self.difficulty_menu = tk.OptionMenu(
            self.difficulty_frame,
            self.difficulty_var,
            *AI_DIFFICULTY_DEPTHS.keys()
        )
        self.difficulty_menu.config(
            font=("Segoe UI", 10),
            bg=THEME["btn_bg"],
            fg=THEME["text"],
            activebackground=THEME["btn_active"],
            activeforeground="#FFFFFF",
            highlightthickness=0,
            bd=0,
            cursor="hand2"
        )
        self.difficulty_menu["menu"].config(
            bg=THEME["card"],
            fg=THEME["text"],
            activebackground=THEME["accent_blue"],
            activeforeground="#FFFFFF"
        )
        self.difficulty_menu.pack(side="right", fill="x", expand=True, padx=(8, 0))

        self.review_frame = tk.Frame(self.history_frame, bg=THEME["sidebar"])
        self.review_frame.pack(fill="x", padx=12, pady=(0, 8))

        self.back_button = tk.Button(
            self.review_frame,
            text="◀ Back",
            font=("Segoe UI", 10, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["text"],
            activebackground=THEME["btn_active"],
            activeforeground="#FFFFFF",
            disabledforeground="#6B7280",
            relief="flat",
            bd=0,
            pady=6,
            cursor="hand2",
            command=self.step_back,
            state="disabled"
        )
        self.back_button.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.forward_button = tk.Button(
            self.review_frame,
            text="Next ▶",
            font=("Segoe UI", 10, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["text"],
            activebackground=THEME["btn_active"],
            activeforeground="#FFFFFF",
            disabledforeground="#6B7280",
            relief="flat",
            bd=0,
            pady=6,
            cursor="hand2",
            command=self.step_forward,
            state="disabled"
        )
        self.forward_button.pack(side="left", fill="x", expand=True, padx=3)

        self.live_button = tk.Button(
            self.review_frame,
            text="⏭ Live",
            font=("Segoe UI", 10, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["text"],
            activebackground=THEME["btn_active"],
            activeforeground="#FFFFFF",
            disabledforeground="#6B7280",
            relief="flat",
            bd=0,
            pady=6,
            cursor="hand2",
            command=self.jump_to_live,
            state="disabled"
        )
        self.live_button.pack(side="left", fill="x", expand=True, padx=(3, 0))

        self.action_frame = tk.Frame(self.history_frame, bg=THEME["sidebar"])
        self.action_frame.pack(fill="x", padx=12, pady=(0, 12))

        self.resign_button = tk.Button(
            self.action_frame,
            text="🏳 Resign",
            font=("Segoe UI", 11, "bold"),
            bg=THEME["accent_red"],
            fg="#FFFFFF",
            activebackground="#B91C1C",
            activeforeground="#FFFFFF",
            disabledforeground="#FCA5A5",
            relief="flat",
            bd=0,
            pady=8,
            cursor="hand2",
            command=self.resign_game,
            state="disabled"
        )
        self.resign_button.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.new_game_button = tk.Button(
            self.action_frame,
            text="⟳ New Game",
            font=("Segoe UI", 11, "bold"),
            bg=THEME["accent_blue"],
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            disabledforeground="#93C5FD",
            relief="flat",
            bd=0,
            pady=8,
            cursor="hand2",
            command=self.new_game
        )
        self.new_game_button.pack(side="left", fill="x", expand=True, padx=(4, 0))

        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Button-1>", self.on_click)

        self._refresh_mode_buttons()
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
                engine_eval = get_engine_evaluation(self.engine)

            if not self.closing:
                self.root.after(
                    0,
                    lambda: self._finish_initial_load(
                        board, moves, status, turn, engine_eval
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

    def _finish_initial_load(self, board, moves, status, turn, engine_eval):
        self.update_position(
            board, moves, status, turn, engine_eval=engine_eval
        )
        if self.prompt_mode_on_start and not self.closing:
            selected = self.choose_game_mode(allow_cancel=False)
            if selected in GAME_MODE_LABELS:
                self.set_game_mode(selected)

    def _refresh_mode_buttons(self):
        if self.closing:
            return
        if self.game_mode == MODE_PVAI:
            self.pvai_mode_btn.config(
                bg=THEME["accent_blue"], fg="#FFFFFF"
            )
            self.pvp_mode_btn.config(
                bg=THEME["btn_bg"], fg=THEME["muted"]
            )
        else:
            self.pvai_mode_btn.config(
                bg=THEME["btn_bg"], fg=THEME["muted"]
            )
            self.pvp_mode_btn.config(
                bg=THEME["accent_green"], fg="#FFFFFF"
            )

    def select_mode_from_sidebar(self, mode):
        if self.engine_busy or mode not in GAME_MODE_LABELS:
            return
        if mode == self.game_mode:
            return
        if not self.move_history:
            self.set_game_mode(mode)
            return
        if messagebox.askyesno(
            "Switch Game Mode",
            f"Start a new game in {GAME_MODE_LABELS[mode]}?"
        ):
            self.new_game(mode=mode)

    def set_game_mode(self, mode):
        if mode not in GAME_MODE_LABELS:
            return
        self.game_mode = mode
        self.mode_label.config(text=f"Mode: {GAME_MODE_LABELS[mode]}")
        self._refresh_mode_buttons()
        self._update_controls()
        self.draw_board()

    def choose_game_mode(self, allow_cancel=True):
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Game Mode")
        dialog.resizable(False, False)
        dialog.configure(bg=THEME["sidebar"])
        dialog.transient(self.root)
        dialog.grab_set()

        chosen = {"mode": None if allow_cancel else self.game_mode}

        tk.Label(
            dialog,
            text="♟ Choose Game Mode",
            font=("Segoe UI", 15, "bold"),
            fg=THEME["text"],
            bg=THEME["sidebar"],
            padx=24,
            pady=(16, 4)
        ).pack()

        tk.Label(
            dialog,
            text=(
                "Player vs AI (PvAI): You play White against Gambit AI.\n"
                "Player vs Player (PvP): Humans control both White and Black."
            ),
            font=("Segoe UI", 10),
            fg=THEME["muted"],
            bg=THEME["sidebar"],
            justify="center",
            padx=24,
            pady=(0, 14)
        ).pack()

        btn_frame = tk.Frame(dialog, bg=THEME["sidebar"], padx=24, pady=8)
        btn_frame.pack(fill="x")

        def select(mode):
            chosen["mode"] = mode
            dialog.destroy()

        tk.Button(
            btn_frame,
            text="Player vs AI (PvAI)",
            font=("Segoe UI", 11, "bold"),
            bg=THEME["accent_blue"],
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            pady=8,
            cursor="hand2",
            command=lambda: select(MODE_PVAI)
        ).pack(fill="x", pady=4)

        tk.Button(
            btn_frame,
            text="Player vs Player (PvP)",
            font=("Segoe UI", 11, "bold"),
            bg=THEME["accent_green"],
            fg="#FFFFFF",
            activebackground="#047857",
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            pady=8,
            cursor="hand2",
            command=lambda: select(MODE_PVP)
        ).pack(fill="x", pady=4)

        if allow_cancel:
            tk.Button(
                btn_frame,
                text="Cancel",
                font=("Segoe UI", 10),
                bg=THEME["btn_bg"],
                fg=THEME["text"],
                activebackground=THEME["btn_active"],
                activeforeground="#FFFFFF",
                relief="flat",
                bd=0,
                pady=6,
                cursor="hand2",
                command=dialog.destroy
            ).pack(fill="x", pady=(8, 8))

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{max(0, x)}+{max(0, y)}")
        dialog.lift()
        dialog.focus_force()

        self.root.wait_window(dialog)
        return chosen["mode"]

    def get_ai_depth(self):
        return AI_DIFFICULTY_DEPTHS.get(self.difficulty_var.get(), 3)

    def get_ai_time_limit(self):
        return AI_DIFFICULTY_TIME_LIMITS.get(self.difficulty_var.get(), 2.0)

    def is_viewing_live(self):
        return (
            not self.position_history
            or self.view_index == len(self.position_history) - 1
        )

    def _update_controls(self):
        if self.closing:
            return
        state = "disabled" if self.engine_busy else "normal"
        self.new_game_button.config(state=state)
        self.pvai_mode_btn.config(state=state)
        self.pvp_mode_btn.config(state=state)
        ai_state = (
            "normal"
            if (not self.engine_busy and self.game_mode == MODE_PVAI)
            else "disabled"
        )
        self.difficulty_menu.config(state=ai_state)

        can_resign = (
            not self.engine_busy
            and not self.animating
            and bool(self.board)
            and self.is_viewing_live()
            and self.game_status not in GAME_OVER_STATUSES
        )
        self.resign_button.config(
            state="normal" if can_resign else "disabled"
        )

        can_back = (
            not self.engine_busy
            and len(self.position_history) > 1
            and self.view_index > 0
        )
        can_forward = (
            not self.engine_busy
            and len(self.position_history) > 1
            and self.view_index < len(self.position_history) - 1
        )
        self.back_button.config(
            state="normal" if can_back else "disabled"
        )
        self.forward_button.config(
            state="normal" if can_forward else "disabled"
        )
        self.live_button.config(
            state="normal" if can_forward else "disabled"
        )

    def _draw_eval_bar(self, score):
        bar_width = self.eval_bar.winfo_width()
        bar_height = self.eval_bar.winfo_height()
        if bar_width <= 1 or bar_height <= 1:
            return

        self.eval_bar.delete("all")
        ratio = compute_advantage_ratio(score)
        split_x = int(bar_width * ratio)

        self.eval_bar.create_rectangle(
            0, 0, split_x, bar_height,
            fill="#F9FAFB",
            outline=""
        )
        self.eval_bar.create_rectangle(
            split_x, 0, bar_width, bar_height,
            fill="#1F2937",
            outline=""
        )
        mid_x = bar_width // 2
        self.eval_bar.create_line(
            mid_x, 0, mid_x, bar_height,
            fill="#DC2626",
            width=1
        )

    def update_evaluation_panel(self, board, engine_eval=None):
        if self.closing or not board:
            return

        if engine_eval is not None:
            self.engine_eval = engine_eval

        material = analyze_material(board)
        material_score = material["score"]
        self.current_material_score = material_score

        headline, side, _ = format_evaluation_summary(material_score)
        dark_colors = {
            "WHITE": "#4ADE80",
            "BLACK": "#F87171",
            "EQUAL": "#E5E7EB",
        }
        self.eval_headline_label.config(
            text=headline,
            fg=dark_colors.get(side, "#E5E7EB")
        )
        self._draw_eval_bar(material_score)

        cpp_score = self.engine_eval if engine_eval is None else engine_eval
        cpp_sign = "+" if cpp_score > 0 else ""
        self.engine_eval_label.config(
            text=f"C++ Engine Eval (material-only): {cpp_sign}{cpp_score:.1f}"
        )

        ai_pawns = evaluate_board(board) / 100.0
        ai_sign = "+" if ai_pawns > 0 else ""
        self.ai_eval_label.config(
            text=f"AI Positional Eval (Material + PST): {ai_sign}{ai_pawns:.2f}"
        )

        wc = material["white_counts"]
        bc = material["black_counts"]
        self.white_material_label.config(
            text=(
                f"White: Q:{wc['Q']}  R:{wc['R']}  "
                f"B:{wc['B']}  N:{wc['N']}  P:{wc['P']}"
            )
        )
        self.black_material_label.config(
            text=(
                f"Black: q:{bc['Q']}  r:{bc['R']}  "
                f"b:{bc['B']}  n:{bc['N']}  p:{bc['P']}"
            )
        )

        mat_sign = "+" if material_score > 0 else ""
        self.material_diff_label.config(
            text=(
                f"{material['explanation']} "
                f"({mat_sign}{material_score:.1f} pts)"
            )
        )

    def update_position(
        self,
        board,
        moves,
        status,
        turn,
        last_move=None,
        appended_move=None,
        keep_busy=False,
        engine_eval=None
    ):
        if self.closing:
            return

        self._cancel_animation()
        self.board = [row[:] for row in board]
        self.legal_moves = moves
        self.game_status = status
        self.white_turn = turn == "WHITE"
        if last_move is not None:
            self.last_move = last_move
        if appended_move is not None:
            self.move_history.append(appended_move)

        snapshot = {
            "board": [row[:] for row in board],
            "status": status,
            "white_turn": (turn == "WHITE"),
            "last_move": self.last_move,
            "engine_eval": self.engine_eval if engine_eval is None else engine_eval,
        }
        if appended_move is not None or not self.position_history:
            self.position_history.append(snapshot)
        else:
            self.position_history[-1] = snapshot
        self.view_index = len(self.position_history) - 1

        if appended_move is not None:
            self.update_move_history()

        self.engine_busy = keep_busy

        self.update_evaluation_panel(board, engine_eval=engine_eval)
        self._update_controls()
        self.draw_board()

    # ---------------- MOVE SELECTION ----------------

    def on_click(self, event):

        if self.engine_busy or self.animating:
            return

        if not self.is_viewing_live():
            return

        if self.game_status in GAME_OVER_STATUSES:
            return

        if not can_human_interact(self.game_mode, self.white_turn):
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

            if not is_own_piece(piece, self.white_turn):
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

                if is_own_piece(piece, self.white_turn):

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
        dialog.configure(bg=THEME["sidebar"])
        dialog.transient(self.root)
        dialog.grab_set()

        selected_move = {"value": None}

        tk.Label(
            dialog,
            text="Choose promotion piece:",
            font=("Segoe UI", 12, "bold"),
            fg=THEME["text"],
            bg=THEME["sidebar"],
            padx=18,
            pady=(14, 6)
        ).pack()

        button_frame = tk.Frame(dialog, bg=THEME["sidebar"], padx=14, pady=12)
        button_frame.pack()

        if self.white_turn:
            labels = [
                ("q", "♕ Queen"),
                ("r", "♖ Rook"),
                ("b", "♗ Bishop"),
                ("n", "♘ Knight"),
            ]
        else:
            labels = [
                ("q", "♛ Queen"),
                ("r", "♜ Rook"),
                ("b", "♝ Bishop"),
                ("n", "♞ Knight"),
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
                    bg=THEME["btn_bg"],
                    fg=THEME["text"],
                    activebackground=THEME["accent_blue"],
                    activeforeground="#FFFFFF",
                    relief="flat",
                    bd=0,
                    width=10,
                    pady=6,
                    cursor="hand2",
                    command=lambda k=key: select_piece(k)
                ).pack(side="left", padx=4)

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        dialog.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{max(0, x)}+{max(0, y)}")
        dialog.lift()
        dialog.focus_force()

        self.root.wait_window(dialog)
        return selected_move["value"]

    # ---------------- HUMAN MOVE ----------------

    def make_move(self, move):

        if (
            self.engine_busy
            or self.animating
            or not self.is_viewing_live()
            or self.game_status in GAME_OVER_STATUSES
        ):
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
                engine_eval = get_engine_evaluation(self.engine)

            game_over = status in GAME_OVER_STATUSES
            should_ai_move = (
                (self.game_mode == MODE_PVAI)
                and (not game_over)
                and (turn == "BLACK")
            )

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
                        keep_busy=should_ai_move,
                        engine_eval=engine_eval
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
            if self.game_mode != MODE_PVAI or status in GAME_OVER_STATUSES:
                if not self.closing:
                    self.root.after(
                        0,
                        lambda: self.update_position(
                            board, moves, status, turn
                        )
                    )
                return

            depth = self.get_ai_depth()
            time_limit = self.get_ai_time_limit()

            with self.engine_lock:
                ai_move = self.ai.find_best_move(
                    board,
                    moves,
                    turn,
                    depth=depth,
                    time_limit=time_limit
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
                engine_eval = get_engine_evaluation(self.engine)

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
                        keep_busy=False,
                        engine_eval=engine_eval
                    )
                )

        except Exception as e:
            if not self.closing:
                self.root.after(
                    0,
                    lambda err=str(e): self._handle_move_error("AI Error", err)
                )

    # ---------------- RESIGN, REPLAY & NEW GAME ----------------

    def resign_game(self, confirm=True):
        if (
            self.engine_busy
            or self.animating
            or not self.board
            or not self.is_viewing_live()
            or self.game_status in GAME_OVER_STATUSES
        ):
            return

        resigning_side = "White" if self.white_turn else "Black"
        if confirm:
            ok = messagebox.askyesno(
                "Resign Game",
                f"{resigning_side} will resign and forfeit the game.\n\nAre you sure?"
            )
            if not ok:
                return

        self.selected_square = None
        self.selected_moves = []
        self.game_status = (
            "RESIGNED_WHITE" if self.white_turn else "RESIGNED_BLACK"
        )
        if self.position_history:
            self.position_history[-1]["status"] = self.game_status
        self._update_controls()
        self.draw_board()

    def _cancel_animation(self):
        if self._anim_after_id is not None:
            try:
                self.root.after_cancel(self._anim_after_id)
            except Exception:
                pass
            self._anim_after_id = None
        if self.animating:
            self.animating = False
            pending = getattr(self, "_pending_target_index", None)
            self._pending_target_index = None
            if pending is not None and 0 <= pending < len(self.position_history):
                self._apply_view_index(pending)

    def _apply_view_index(self, idx):
        if self.closing or not (0 <= idx < len(self.position_history)):
            return

        self.view_index = idx
        snapshot = self.position_history[idx]
        self.board = [row[:] for row in snapshot["board"]]
        self.game_status = snapshot["status"]
        self.white_turn = snapshot["white_turn"]
        self.last_move = snapshot["last_move"]
        self.selected_square = None
        self.selected_moves = []

        self.update_evaluation_panel(
            self.board,
            engine_eval=snapshot["engine_eval"]
        )
        self._highlight_history_for_view(idx)
        self._update_controls()
        self.draw_board()

    def _highlight_history_for_view(self, idx):
        self.history_list.selection_clear(0, tk.END)
        if idx > 0:
            list_row = (idx - 1) // 2
            if 0 <= list_row < self.history_list.size():
                self.history_list.selection_set(list_row)
                self.history_list.see(list_row)

    def _animate_move_step(
        self,
        target_index,
        target_board,
        moving_piece,
        from_sq,
        to_sq,
        step=0,
        total_steps=8
    ):
        if self.closing:
            return

        if step >= total_steps:
            self.animating = False
            self._anim_after_id = None
            self._pending_target_index = None
            self._apply_view_index(target_index)
            return

        self.animating = True
        self._pending_target_index = target_index
        self.board = [row[:] for row in target_board]
        self.last_move = self.position_history[target_index]["last_move"]
        self.selected_square = None
        self.selected_moves = []

        self.draw_board(hidden_square=to_sq, view_index_override=target_index)

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        _, square_size, offset_x, offset_y = get_board_geometry(width, height)

        from_r, from_c = notation_to_coords(from_sq)
        to_r, to_c = notation_to_coords(to_sq)
        x_start = offset_x + (from_c + 0.5) * square_size
        y_start = offset_y + (from_r + 0.5) * square_size
        x_end = offset_x + (to_c + 0.5) * square_size
        y_end = offset_y + (to_r + 0.5) * square_size

        t = step / total_steps
        ease = 1.0 - (1.0 - t) ** 2
        cur_x = x_start + (x_end - x_start) * ease
        cur_y = y_start + (y_end - y_start) * ease

        if moving_piece not in (".", " "):
            self.draw_piece(moving_piece, cur_x, cur_y, square_size)

        self._anim_after_id = self.root.after(
            15,
            lambda: self._animate_move_step(
                target_index,
                target_board,
                moving_piece,
                from_sq,
                to_sq,
                step=step + 1,
                total_steps=total_steps
            )
        )

    def step_back(self, animate=True):
        if self.engine_busy or not self.position_history:
            return

        self._cancel_animation()
        if self.view_index <= 0:
            return

        cur_idx = self.view_index
        target_idx = cur_idx - 1
        move = self.position_history[cur_idx]["last_move"]

        if animate and move and len(move) >= 4:
            start_sq = move[:2]
            end_sq = move[2:4]
            end_r, end_c = notation_to_coords(end_sq)
            start_r, start_c = notation_to_coords(start_sq)
            target_board = self.position_history[target_idx]["board"]
            moving_piece = self.position_history[cur_idx]["board"][end_r][end_c]
            if moving_piece in (".", " "):
                moving_piece = target_board[start_r][start_c]
            self._animate_move_step(
                target_idx,
                target_board,
                moving_piece,
                end_sq,
                start_sq,
            )
        else:
            self._apply_view_index(target_idx)

    def step_forward(self, animate=True):
        if self.engine_busy or not self.position_history:
            return

        self._cancel_animation()
        if self.view_index >= len(self.position_history) - 1:
            return

        cur_idx = self.view_index
        target_idx = cur_idx + 1
        move = self.position_history[target_idx]["last_move"]

        if animate and move and len(move) >= 4:
            start_sq = move[:2]
            end_sq = move[2:4]
            start_r, start_c = notation_to_coords(start_sq)
            end_r, end_c = notation_to_coords(end_sq)
            target_board = self.position_history[target_idx]["board"]
            moving_piece = self.position_history[cur_idx]["board"][start_r][start_c]
            if moving_piece in (".", " "):
                moving_piece = target_board[end_r][end_c]
            self._animate_move_step(
                target_idx,
                target_board,
                moving_piece,
                start_sq,
                end_sq,
            )
        else:
            self._apply_view_index(target_idx)

    def jump_to_live(self):
        if self.engine_busy or not self.position_history:
            return
        self._cancel_animation()
        self._apply_view_index(len(self.position_history) - 1)

    def new_game(self, mode=None, prompt_mode=None):

        if self.engine_busy:
            return

        if mode in GAME_MODE_LABELS:
            selected_mode = mode
        elif prompt_mode is True or (prompt_mode is None and self.prompt_mode_on_start):
            selected_mode = self.choose_game_mode(allow_cancel=True)
            if selected_mode not in GAME_MODE_LABELS:
                return
        else:
            selected_mode = self.game_mode

        self.engine_busy = True
        self._update_controls()

        threading.Thread(
            target=self.send_new_game,
            args=(selected_mode,),
            daemon=True
        ).start()

    def send_new_game(self, selected_mode=None):

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
                engine_eval = get_engine_evaluation(self.engine)

            if not self.closing:
                self.root.after(
                    0,
                    lambda: self._apply_new_game_state(
                        board, moves, status, turn, engine_eval, selected_mode
                    )
                )

        except Exception as e:
            if not self.closing:
                self.root.after(
                    0,
                    lambda err=str(e): self._handle_move_error("New Game Error", err)
                )

    def _apply_new_game_state(
        self,
        board,
        moves,
        status,
        turn,
        engine_eval=None,
        selected_mode=None
    ):
        if self.closing:
            return

        if selected_mode in GAME_MODE_LABELS:
            self.game_mode = selected_mode
            self.mode_label.config(text=f"Mode: {GAME_MODE_LABELS[selected_mode]}")
            self._refresh_mode_buttons()

        self._cancel_animation()
        self.selected_square = None
        self.selected_moves = []
        self.last_move = None
        self.move_history = []
        self.position_history = []
        self.view_index = -1
        self.update_move_history()
        self.update_position(board, moves, status, turn, engine_eval=engine_eval)

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

    def draw_board(self, hidden_square=None, view_index_override=None):

        if not self.board:
            return

        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        active_view_index = (
            self.view_index if view_index_override is None else view_index_override
        )
        viewing_live = (
            not self.position_history
            or active_view_index == len(self.position_history) - 1
        )

        if not viewing_live:
            turn_text = (
                f"Reviewing Move {active_view_index} / "
                f"{len(self.position_history) - 1} — Click Next or Live"
            )
            status_color = "#FBBF24"
        else:
            turn_text, status_color = format_status_text(
                self.game_status,
                self.white_turn,
                self.engine_busy,
                game_mode=self.game_mode
            )

        self.canvas.create_text(
            width / 2,
            22,
            text=turn_text,
            font=("Arial", 16, "bold"),
            fill=status_color
        )

        board_size, square_size, offset_x, offset_y = get_board_geometry(width, height)

        self.canvas.create_rectangle(
            offset_x - 6,
            offset_y - 6,
            offset_x + board_size + 6,
            offset_y + board_size + 6,
            fill="#2B303B",
            outline="#3F4656",
            width=2
        )

        light = "#EEEED2"
        dark = "#769656"
        selected_color = "#F6F669"
        last_move_light = "#F5F682"
        last_move_dark = "#BACA44"
        check_color = "#E05252"

        legal_targets = {
            move[2:4]
            for move in self.selected_moves
        }

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

                is_light = (row + col) % 2 == 0
                color = light if is_light else dark

                square = self.square_to_notation(
                    row, col
                )

                if self.last_move is not None:
                    if (
                        square == self.last_move[:2]
                        or square == self.last_move[2:4]
                    ):
                        color = last_move_light if is_light else last_move_dark

                if square == king_in_check_square:
                    color = check_color

                if square == self.selected_square:
                    color = selected_color

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline=""
                )

                piece = self.board[row][col]
                has_piece = piece != "." and piece != " "

                if square in legal_targets:
                    cx = x1 + square_size / 2
                    cy = y1 + square_size / 2
                    if has_piece:
                        ring_pad = square_size * 0.08
                        self.canvas.create_oval(
                            x1 + ring_pad,
                            y1 + ring_pad,
                            x2 - ring_pad,
                            y2 - ring_pad,
                            outline="#3D5A2A",
                            width=max(3, int(square_size * 0.08))
                        )
                    else:
                        dot_r = square_size * 0.16
                        self.canvas.create_oval(
                            cx - dot_r,
                            cy - dot_r,
                            cx + dot_r,
                            cy + dot_r,
                            fill="#4A6B35" if not is_light else "#7B9361",
                            outline=""
                        )

                if has_piece and square != hidden_square:

                    self.draw_piece(
                        piece,
                        x1 + square_size / 2,
                        y1 + square_size / 2,
                        square_size
                    )

                if col == 0:

                    self.canvas.create_text(
                        x1 + 6,
                        y1 + 5,
                        text=str(8 - row),
                        anchor="nw",
                        font=("Segoe UI", 10, "bold"),
                        fill=dark if is_light else light
                    )

                if row == 7:

                    self.canvas.create_text(
                        x2 - 6,
                        y2 - 4,
                        text=chr(ord("a") + col),
                        anchor="se",
                        font=("Segoe UI", 10, "bold"),
                        fill=dark if is_light else light
                    )

    def draw_piece(self, piece, x, y, square_size):

        solid_pieces = {
            "K": "♚",
            "Q": "♛",
            "R": "♜",
            "B": "♝",
            "N": "♞",
            "P": "♟",
            "k": "♚",
            "q": "♛",
            "r": "♜",
            "b": "♝",
            "n": "♞",
            "p": "♟",
        }

        symbol = solid_pieces.get(piece, "")
        if not symbol:
            return

        font_size = max(
            20,
            int(square_size * 0.70)
        )

        is_white = piece.isupper()
        fill_color = "#FFFFFF" if is_white else "#18181B"
        outline_color = "#1E293B" if is_white else "#D1D5DB"
        offset = max(1, int(square_size * 0.02))

        if is_white:
            for dx, dy in ((-offset, 0), (offset, 0), (0, -offset), (0, offset)):
                self.canvas.create_text(
                    x + dx,
                    y + dy,
                    text=symbol,
                    font=("Segoe UI Symbol", font_size),
                    fill=outline_color
                )
        else:
            self.canvas.create_text(
                x + 1,
                y + 1,
                text=symbol,
                font=("Segoe UI Symbol", font_size),
                fill=outline_color
            )

        self.canvas.create_text(
            x,
            y,
            text=symbol,
            font=("Segoe UI Symbol", font_size),
            fill=fill_color
        )

    # ---------------- SHUTDOWN ----------------

    def close(self):
        self.closing = True
        self._cancel_animation()

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
