
import random
import subprocess
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox

from ai import (
    AI,
    get_cpp_best_move,
    get_engine_evaluation,
    get_fen,
    get_position,
    send_move_to_engine,
    set_fen,
)
from chess_utils import (
    STANDARD_START_FEN,
    build_pgn,
    format_captured_tray,
    format_san_move,
    get_captured_piece,
    play_sound,
)
from evaluation import (
    analyze_material,
    evaluate_board,
    format_evaluation_summary,
)


GAME_OVER_STATUSES = (
    "CHECKMATE",
    "STALEMATE",
    "DRAW_INSUFFICIENT_MATERIAL",
    "DRAW_FIFTY_MOVE",
    "DRAW_THREEFOLD_REPETITION",
    "DRAW_AGREED",
    "RESIGNED_WHITE",
    "RESIGNED_BLACK",
    "TIMEOUT_WHITE",
    "TIMEOUT_BLACK",
)

MODE_PVP = "PvP"
MODE_PVAI = "PvAI"

HUMAN_COLOR_WHITE = "WHITE"
HUMAN_COLOR_BLACK = "BLACK"

GAME_MODE_LABELS = {
    MODE_PVP: "Player vs Player (PvP)",
    MODE_PVAI: "Player vs AI (PvAI)",
}

TIME_CONTROLS = {
    "Untimed": None,
    "Bullet (1+0)": (60, 0),
    "Blitz (3+2)": (180, 2),
    "Rapid (10+0)": (600, 0),
}

AI_DIFFICULTY_DEPTHS = {
    "Easy (Depth 2)": 2,
    "Medium (Depth 4)": 4,
    "Hard (Depth 6)": 6,
}

AI_DIFFICULTY_TIME_LIMITS = {
    "Easy (Depth 2)": 0.4,
    "Medium (Depth 4)": 1.5,
    "Hard (Depth 6)": 2.5,
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


def can_human_interact(game_mode, white_turn, human_color=HUMAN_COLOR_WHITE):
    if game_mode == MODE_PVP:
        return True
    return white_turn if human_color == HUMAN_COLOR_WHITE else (not white_turn)


def should_ai_move_for_turn(game_mode, status, turn, human_color=HUMAN_COLOR_WHITE):
    if game_mode != MODE_PVAI or status in GAME_OVER_STATUSES:
        return False
    return turn != human_color


def board_to_display_coords(row, col, flipped=False):
    return (7 - row, 7 - col) if flipped else (row, col)


def display_to_board_coords(disp_row, disp_col, flipped=False):
    return (7 - disp_row, 7 - disp_col) if flipped else (disp_row, disp_col)


def format_clock_time(seconds):
    if seconds is None:
        return "∞"
    seconds = max(0.0, float(seconds))
    if seconds < 10.0:
        return f"0:{seconds:04.1f}"
    total_secs = int(seconds)
    mins, secs = divmod(total_secs, 60)
    return f"{mins:02d}:{secs:02d}"


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


def format_status_text(
    game_status,
    white_turn,
    engine_busy,
    game_mode=MODE_PVAI,
    human_color=HUMAN_COLOR_WHITE
):
    ai_turn = (
        game_mode == MODE_PVAI
        and ((white_turn and human_color == HUMAN_COLOR_BLACK)
             or ((not white_turn) and human_color == HUMAN_COLOR_WHITE))
    )
    if ai_turn and engine_busy and game_status not in GAME_OVER_STATUSES:
        side = "White" if white_turn else "Black"
        return f"{side} — AI thinking...", "#60A5FA"

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

    if game_status == "DRAW_FIFTY_MOVE":
        return "DRAW — 50-Move Rule", "#FBBF24"

    if game_status == "DRAW_THREEFOLD_REPETITION":
        return "DRAW — Threefold Repetition", "#FBBF24"

    if game_status == "DRAW_AGREED":
        return "DRAW — Agreed", "#FBBF24"

    if game_status == "RESIGNED_WHITE":
        return "White resigned — Black wins", "#F87171"

    if game_status == "RESIGNED_BLACK":
        return "Black resigned — White wins", "#F87171"

    if game_status == "TIMEOUT_WHITE":
        return "Time out — Black wins", "#F87171"

    if game_status == "TIMEOUT_BLACK":
        return "Time out — White wins", "#F87171"

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

    def __init__(
        self,
        root,
        game_mode=None,
        prompt_mode_on_start=True,
        human_color=HUMAN_COLOR_WHITE,
        time_control="Untimed"
    ):
        self.root = root
        self.root.title("Gambit Chess")
        self.root.minsize(880, 620)
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
        self.human_color = (
            human_color
            if human_color in (HUMAN_COLOR_WHITE, HUMAN_COLOR_BLACK)
            else HUMAN_COLOR_WHITE
        )
        self.board_flipped = (
            self.game_mode == MODE_PVAI
            and self.human_color == HUMAN_COLOR_BLACK
        )
        self.time_control_name = (
            time_control if time_control in TIME_CONTROLS else "Untimed"
        )
        self.white_time = None
        self.black_time = None
        self._clock_last_tick = None
        self._clock_after_id = None
        self._in_modal = False

        self.engine_eval = 0

        self.board = []
        self.legal_moves = []
        self.selected_square = None
        self.selected_moves = []
        self.last_move = None
        self.white_turn = True
        self.move_history = []
        self.san_history = []
        self.captured_by_white = []
        self.captured_by_black = []
        self.initial_fen = STANDARD_START_FEN
        self.position_history = []
        self.view_index = -1
        self.animating = False
        self._anim_after_id = None
        self._pending_live_animate = False
        self._drag_state = None
        self.hint_move = None
        self.sound_enabled = bool(prompt_mode_on_start)
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
        self.header_frame.pack(fill="x", padx=12, pady=(8, 6))

        self.title_row = tk.Frame(self.header_frame, bg=THEME["sidebar"])
        self.title_row.pack(fill="x")

        tk.Label(
            self.title_row,
            text="♟ GAMBIT CHESS",
            font=("Segoe UI", 13, "bold"),
            fg=THEME["text"],
            bg=THEME["sidebar"],
            anchor="w"
        ).pack(side="left")

        self.fen_button = tk.Button(
            self.title_row,
            text="FEN",
            font=("Segoe UI", 8, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["text"],
            activebackground=THEME["btn_active"],
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=6,
            pady=2,
            cursor="hand2",
            command=self.prompt_load_fen
        )
        self.fen_button.pack(side="right", padx=(3, 0))

        self.pgn_button = tk.Button(
            self.title_row,
            text="PGN",
            font=("Segoe UI", 8, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["text"],
            activebackground=THEME["btn_active"],
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=6,
            pady=2,
            cursor="hand2",
            command=self.export_pgn
        )
        self.pgn_button.pack(side="right", padx=(3, 0))

        self.sound_button = tk.Button(
            self.title_row,
            text="🔊" if self.sound_enabled else "🔇",
            font=("Segoe UI", 9),
            bg=THEME["btn_bg"],
            fg=THEME["text"],
            activebackground=THEME["btn_active"],
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=5,
            pady=1,
            cursor="hand2",
            command=self.toggle_sound
        )
        self.sound_button.pack(side="right")

        self.mode_label = tk.Label(
            self.header_frame,
            text=f"Mode: {GAME_MODE_LABELS[self.game_mode]}",
            font=("Segoe UI", 9, "bold"),
            fg="#93C5FD",
            bg=THEME["sidebar"],
            anchor="w"
        )
        self.mode_label.pack(fill="x", pady=(1, 4))

        self.mode_switch_frame = tk.Frame(self.header_frame, bg=THEME["sidebar"])
        self.mode_switch_frame.pack(fill="x")

        self.pvai_mode_btn = tk.Button(
            self.mode_switch_frame,
            text="Player vs AI",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            pady=5,
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
            pady=5,
            cursor="hand2",
            command=lambda: self.select_mode_from_sidebar(MODE_PVP)
        )
        self.pvp_mode_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # ---- Clocks Card ----
        self.clock_frame = tk.Frame(
            self.history_frame,
            bg=THEME["card"],
            highlightthickness=1,
            highlightbackground=THEME["border"],
            padx=6,
            pady=4
        )
        self.clock_frame.pack(fill="x", padx=12, pady=(0, 6))

        self.top_clock_box = tk.Frame(self.clock_frame, bg=THEME["list_bg"], padx=8, pady=3)
        self.top_clock_box.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.top_clock_name = tk.Label(
            self.top_clock_box,
            text="Black",
            font=("Segoe UI", 9, "bold"),
            fg=THEME["muted"],
            bg=THEME["list_bg"],
            anchor="w"
        )
        self.top_clock_name.pack(fill="x")

        self.top_clock_time = tk.Label(
            self.top_clock_box,
            text="∞",
            font=("Consolas", 12, "bold"),
            fg=THEME["text"],
            bg=THEME["list_bg"],
            anchor="w"
        )
        self.top_clock_time.pack(fill="x")

        self.top_captured_label = tk.Label(
            self.top_clock_box,
            text="—",
            font=("Segoe UI Symbol", 9),
            fg="#CBD5E1",
            bg=THEME["list_bg"],
            anchor="w"
        )
        self.top_captured_label.pack(fill="x")

        self.bottom_clock_box = tk.Frame(self.clock_frame, bg=THEME["list_bg"], padx=8, pady=3)
        self.bottom_clock_box.pack(side="left", fill="x", expand=True, padx=(3, 0))

        self.bottom_clock_name = tk.Label(
            self.bottom_clock_box,
            text="White",
            font=("Segoe UI", 9, "bold"),
            fg=THEME["muted"],
            bg=THEME["list_bg"],
            anchor="w"
        )
        self.bottom_clock_name.pack(fill="x")

        self.bottom_clock_time = tk.Label(
            self.bottom_clock_box,
            text="∞",
            font=("Consolas", 12, "bold"),
            fg=THEME["text"],
            bg=THEME["list_bg"],
            anchor="w"
        )
        self.bottom_clock_time.pack(fill="x")

        self.bottom_captured_label = tk.Label(
            self.bottom_clock_box,
            text="—",
            font=("Segoe UI Symbol", 9),
            fg="#CBD5E1",
            bg=THEME["list_bg"],
            anchor="w"
        )
        self.bottom_captured_label.pack(fill="x")

        # ---- Evaluation Card ----
        self.eval_frame = tk.LabelFrame(
            self.history_frame,
            text=" Position Evaluation ",
            font=("Segoe UI", 9, "bold"),
            fg=THEME["muted"],
            bg=THEME["card"],
            bd=1,
            relief="solid",
            highlightbackground=THEME["border"],
            padx=8,
            pady=5
        )
        self.eval_frame.pack(fill="x", padx=12, pady=(0, 6))

        self.eval_headline_label = tk.Label(
            self.eval_frame,
            text="Position is equal: 0.0",
            font=("Segoe UI", 11, "bold"),
            fg=THEME["text"],
            bg=THEME["card"],
            anchor="w"
        )
        self.eval_headline_label.pack(fill="x")

        self.eval_bar = tk.Canvas(
            self.eval_frame,
            height=13,
            bg="#111827",
            highlightthickness=1,
            highlightbackground=THEME["border"]
        )
        self.eval_bar.pack(fill="x", pady=(4, 4))
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
        self.ai_eval_label.pack(fill="x", pady=(0, 4))

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
        self.material_diff_label.pack(fill="x", pady=(3, 0))

        # ---- Bottom Controls (packed bottom-first so always visible!) ----
        self.action_frame = tk.Frame(self.history_frame, bg=THEME["sidebar"])
        self.action_frame.pack(side="bottom", fill="x", padx=12, pady=(0, 10))

        self.resign_button = tk.Button(
            self.action_frame,
            text="🏳 Resign",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["accent_red"],
            fg="#FFFFFF",
            activebackground="#B91C1C",
            activeforeground="#FFFFFF",
            disabledforeground="#FCA5A5",
            relief="flat",
            bd=0,
            pady=7,
            cursor="hand2",
            command=self.resign_game,
            state="disabled"
        )
        self.resign_button.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.draw_button = tk.Button(
            self.action_frame,
            text="½ Draw",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["text"],
            activebackground=THEME["btn_active"],
            activeforeground="#FFFFFF",
            disabledforeground="#6B7280",
            relief="flat",
            bd=0,
            pady=7,
            cursor="hand2",
            command=self.offer_draw,
            state="disabled"
        )
        self.draw_button.pack(side="left", fill="x", expand=True, padx=3)

        self.new_game_button = tk.Button(
            self.action_frame,
            text="⟳ New",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["accent_blue"],
            fg="#FFFFFF",
            activebackground="#1D4ED8",
            activeforeground="#FFFFFF",
            disabledforeground="#93C5FD",
            relief="flat",
            bd=0,
            pady=7,
            cursor="hand2",
            command=self.new_game
        )
        self.new_game_button.pack(side="left", fill="x", expand=True, padx=(3, 0))

        self.review_frame = tk.Frame(self.history_frame, bg=THEME["sidebar"])
        self.review_frame.pack(side="bottom", fill="x", padx=12, pady=(0, 6))

        self.back_button = tk.Button(
            self.review_frame,
            text="◀ Back",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["text"],
            activebackground=THEME["btn_active"],
            activeforeground="#FFFFFF",
            disabledforeground="#6B7280",
            relief="flat",
            bd=0,
            pady=5,
            cursor="hand2",
            command=self.step_back,
            state="disabled"
        )
        self.back_button.pack(side="left", fill="x", expand=True, padx=(0, 3))

        self.forward_button = tk.Button(
            self.review_frame,
            text="Next ▶",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["text"],
            activebackground=THEME["btn_active"],
            activeforeground="#FFFFFF",
            disabledforeground="#6B7280",
            relief="flat",
            bd=0,
            pady=5,
            cursor="hand2",
            command=self.step_forward,
            state="disabled"
        )
        self.forward_button.pack(side="left", fill="x", expand=True, padx=3)

        self.live_button = tk.Button(
            self.review_frame,
            text="⏭ Live",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["text"],
            activebackground=THEME["btn_active"],
            activeforeground="#FFFFFF",
            disabledforeground="#6B7280",
            relief="flat",
            bd=0,
            pady=5,
            cursor="hand2",
            command=self.jump_to_live,
            state="disabled"
        )
        self.live_button.pack(side="left", fill="x", expand=True, padx=3)

        self.flip_button = tk.Button(
            self.review_frame,
            text="⇅ Flip",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["text"],
            activebackground=THEME["btn_active"],
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            pady=5,
            cursor="hand2",
            command=self.flip_board
        )
        self.flip_button.pack(side="left", fill="x", expand=True, padx=3)

        self.hint_button = tk.Button(
            self.review_frame,
            text="💡 Hint",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["btn_bg"],
            fg="#FDE047",
            activebackground=THEME["btn_active"],
            activeforeground="#FEF08A",
            disabledforeground="#6B7280",
            relief="flat",
            bd=0,
            pady=5,
            cursor="hand2",
            command=self.request_hint,
            state="disabled"
        )
        self.hint_button.pack(side="left", fill="x", expand=True, padx=(3, 0))

        self.settings_frame = tk.Frame(self.history_frame, bg=THEME["sidebar"])
        self.settings_frame.pack(side="bottom", fill="x", padx=12, pady=(0, 6))

        self.options_row = tk.Frame(self.settings_frame, bg=THEME["sidebar"])
        self.options_row.pack(fill="x", pady=(0, 5))

        tk.Label(
            self.options_row,
            text="Time:",
            font=("Segoe UI", 9, "bold"),
            fg=THEME["text"],
            bg=THEME["sidebar"]
        ).pack(side="left")

        self.time_var = tk.StringVar(value=self.time_control_name)
        self.time_menu = tk.OptionMenu(
            self.options_row,
            self.time_var,
            *TIME_CONTROLS.keys(),
            command=self.on_sidebar_time_change
        )
        self.time_menu.config(
            font=("Segoe UI", 9),
            bg=THEME["btn_bg"],
            fg=THEME["text"],
            activebackground=THEME["btn_active"],
            activeforeground="#FFFFFF",
            highlightthickness=0,
            bd=0,
            cursor="hand2"
        )
        self.time_menu["menu"].config(
            bg=THEME["card"],
            fg=THEME["text"],
            activebackground=THEME["accent_blue"],
            activeforeground="#FFFFFF"
        )
        self.time_menu.pack(side="left", fill="x", expand=True, padx=(4, 8))

        tk.Label(
            self.options_row,
            text="Side:",
            font=("Segoe UI", 9, "bold"),
            fg=THEME["text"],
            bg=THEME["sidebar"]
        ).pack(side="left")

        self.side_var = tk.StringVar(
            value="White" if self.human_color == HUMAN_COLOR_WHITE else "Black"
        )
        self.side_menu = tk.OptionMenu(
            self.options_row,
            self.side_var,
            "White",
            "Black",
            "Random",
            command=self.on_sidebar_side_change
        )
        self.side_menu.config(
            font=("Segoe UI", 9),
            bg=THEME["btn_bg"],
            fg=THEME["text"],
            activebackground=THEME["btn_active"],
            activeforeground="#FFFFFF",
            highlightthickness=0,
            bd=0,
            cursor="hand2"
        )
        self.side_menu["menu"].config(
            bg=THEME["card"],
            fg=THEME["text"],
            activebackground=THEME["accent_blue"],
            activeforeground="#FFFFFF"
        )
        self.side_menu.pack(side="left", padx=(4, 0))

        self.difficulty_frame = tk.Frame(self.settings_frame, bg=THEME["sidebar"])
        self.difficulty_frame.pack(fill="x")

        tk.Label(
            self.difficulty_frame,
            text="AI Level:",
            font=("Segoe UI", 9, "bold"),
            fg=THEME["text"],
            bg=THEME["sidebar"]
        ).pack(side="left")

        self.difficulty_var = tk.StringVar(value="Medium (Depth 4)")
        self.difficulty_menu = tk.OptionMenu(
            self.difficulty_frame,
            self.difficulty_var,
            *AI_DIFFICULTY_DEPTHS.keys()
        )
        self.difficulty_menu.config(
            font=("Segoe UI", 9),
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

        # ---- Move History (fills remaining space cleanly) ----
        self.history_title = tk.Label(
            self.history_frame,
            text="Move History",
            font=("Segoe UI", 10, "bold"),
            fg=THEME["muted"],
            bg=THEME["sidebar"],
            anchor="w"
        )
        self.history_title.pack(fill="x", padx=12, pady=(0, 2))

        self.history_list_frame = tk.Frame(
            self.history_frame,
            bg=THEME["list_bg"],
            highlightthickness=1,
            highlightbackground=THEME["border"]
        )
        self.history_list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        self.history_scroll = tk.Scrollbar(self.history_list_frame)
        self.history_scroll.pack(side="right", fill="y")

        self.history_list = tk.Listbox(
            self.history_list_frame,
            height=4,
            font=("Consolas", 11),
            bg=THEME["list_bg"],
            fg=THEME["text"],
            selectbackground=THEME["accent_blue"],
            selectforeground="#FFFFFF",
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=self.history_scroll.set
        )
        self.history_list.pack(side="left", fill="both", expand=True, padx=6, pady=3)
        self.history_scroll.config(command=self.history_list.yview)

        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        self._reset_clocks(self.time_control_name)
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
            config = self.choose_game_mode(allow_cancel=False)
            if config is not None:
                mode, human_color, time_control = config
                self._apply_game_config(mode, human_color, time_control)
                self._reset_clocks(time_control)
                self._start_clock()
                self._maybe_start_ai_opening()
        else:
            self._reset_clocks(self.time_control_name)
            self._start_clock()
            self._maybe_start_ai_opening()

    def _apply_game_config(self, mode, human_color=HUMAN_COLOR_WHITE, time_control="Untimed"):
        if mode in GAME_MODE_LABELS:
            self.game_mode = mode
        if human_color in (HUMAN_COLOR_WHITE, HUMAN_COLOR_BLACK):
            self.human_color = human_color
        if time_control in TIME_CONTROLS:
            self.time_control_name = time_control
        self.board_flipped = (
            self.game_mode == MODE_PVAI
            and self.human_color == HUMAN_COLOR_BLACK
        )
        side_suffix = ""
        if self.game_mode == MODE_PVAI:
            side_suffix = " (White)" if self.human_color == HUMAN_COLOR_WHITE else " (Black)"
        self.mode_label.config(
            text=f"Mode: {GAME_MODE_LABELS[self.game_mode]}{side_suffix}"
        )
        self.time_var.set(self.time_control_name)
        if hasattr(self, "side_var") and self.side_var.get() != "Random":
            self.side_var.set(
                "White" if self.human_color == HUMAN_COLOR_WHITE else "Black"
            )
        self._refresh_mode_buttons()
        self._refresh_clocks()
        self._update_controls()
        self.draw_board()

    def on_sidebar_time_change(self, choice):
        if self.engine_busy or choice not in TIME_CONTROLS:
            self.time_var.set(self.time_control_name)
            return
        if choice == self.time_control_name:
            return
        if not self.move_history and self.game_status not in GAME_OVER_STATUSES:
            self._reset_clocks(choice)
            self._start_clock()
            return
        if messagebox.askyesno(
            "Change Time Control",
            f"Start a new game with {choice}?"
        ):
            self.new_game(time_control=choice)
        else:
            self.time_var.set(self.time_control_name)

    def on_sidebar_side_change(self, choice):
        if self.engine_busy or self.game_mode != MODE_PVAI:
            self.side_var.set(
                "White" if self.human_color == HUMAN_COLOR_WHITE else "Black"
            )
            return
        if choice == "Random":
            resolved = random.choice((HUMAN_COLOR_WHITE, HUMAN_COLOR_BLACK))
        elif choice == "Black":
            resolved = HUMAN_COLOR_BLACK
        else:
            resolved = HUMAN_COLOR_WHITE

        if not self.move_history and self.game_status not in GAME_OVER_STATUSES:
            self._apply_game_config(
                self.game_mode,
                resolved,
                self.time_control_name
            )
            self.side_var.set(
                "White" if resolved == HUMAN_COLOR_WHITE else "Black"
            )
            self._maybe_start_ai_opening()
            return

        if messagebox.askyesno(
            "Change Side",
            f"Start a new game playing as {choice}?"
        ):
            self.new_game(mode=MODE_PVAI, human_color=resolved)
        else:
            self.side_var.set(
                "White" if self.human_color == HUMAN_COLOR_WHITE else "Black"
            )

    def _maybe_start_ai_opening(self):
        if (
            not self.closing
            and self.game_mode == MODE_PVAI
            and self.human_color == HUMAN_COLOR_BLACK
            and self.white_turn
            and self.game_status not in GAME_OVER_STATUSES
            and not self.engine_busy
        ):
            self.engine_busy = True
            self._update_controls()
            self.draw_board()
            board_copy = [r[:] for r in self.board]
            moves_copy = list(self.legal_moves)
            status_copy = self.game_status
            threading.Thread(
                target=self.process_ai_turn,
                args=(board_copy, moves_copy, status_copy, "WHITE"),
                daemon=True
            ).start()

    def _reset_clocks(self, time_control=None):
        self._stop_clock()
        if time_control in TIME_CONTROLS:
            self.time_control_name = time_control
        spec = TIME_CONTROLS.get(self.time_control_name)
        if spec is None:
            self.white_time = None
            self.black_time = None
        else:
            base_seconds, _ = spec
            self.white_time = float(base_seconds)
            self.black_time = float(base_seconds)
        self._refresh_clocks()

    def _stop_clock(self):
        if self._clock_after_id is not None:
            try:
                self.root.after_cancel(self._clock_after_id)
            except Exception:
                pass
            self._clock_after_id = None
        self._clock_last_tick = None

    def _start_clock(self):
        self._stop_clock()
        if (
            self.closing
            or self._in_modal
            or TIME_CONTROLS.get(self.time_control_name) is None
            or self.game_status in GAME_OVER_STATUSES
        ):
            return
        self._clock_last_tick = time.monotonic()
        self._clock_after_id = self.root.after(100, self._tick_clock)

    def _apply_increment(self, moved_white):
        spec = TIME_CONTROLS.get(self.time_control_name)
        if spec is None or self.game_status in GAME_OVER_STATUSES:
            return
        _, increment = spec
        if increment <= 0:
            return
        if moved_white and self.white_time is not None:
            self.white_time += increment
        elif (not moved_white) and self.black_time is not None:
            self.black_time += increment
        self._refresh_clocks()

    def _tick_clock(self):
        self._clock_after_id = None
        if (
            self.closing
            or self._in_modal
            or TIME_CONTROLS.get(self.time_control_name) is None
            or self.game_status in GAME_OVER_STATUSES
            or not self.board
        ):
            self._clock_last_tick = None
            return

        now = time.monotonic()
        if self._clock_last_tick is not None:
            elapsed = max(0.0, now - self._clock_last_tick)
            if self.white_turn and self.white_time is not None:
                self.white_time = max(0.0, self.white_time - elapsed)
                if self.white_time <= 0.0:
                    self._handle_timeout(True)
                    return
            elif (not self.white_turn) and self.black_time is not None:
                self.black_time = max(0.0, self.black_time - elapsed)
                if self.black_time <= 0.0:
                    self._handle_timeout(False)
                    return

        self._clock_last_tick = now
        self._refresh_clocks()
        self._clock_after_id = self.root.after(100, self._tick_clock)

    def _handle_timeout(self, white_flagged):
        self._stop_clock()
        self.selected_square = None
        self.selected_moves = []
        self.game_status = "TIMEOUT_WHITE" if white_flagged else "TIMEOUT_BLACK"
        if self.position_history:
            self.position_history[-1]["status"] = self.game_status
        self._refresh_clocks()
        self._update_controls()
        if self.is_viewing_live():
            self.draw_board()

    def _refresh_clocks(self):
        if self.closing:
            return
        top_is_white = self.board_flipped
        top_name = "White" if top_is_white else "Black"
        bottom_name = "Black" if top_is_white else "White"
        if self.game_mode == MODE_PVAI:
            if (self.human_color == HUMAN_COLOR_WHITE) == top_is_white:
                top_name += " (You)"
            else:
                top_name += " (AI)"
            if (self.human_color == HUMAN_COLOR_WHITE) != top_is_white:
                bottom_name += " (You)"
            else:
                bottom_name += " (AI)"

        top_val = self.white_time if top_is_white else self.black_time
        bottom_val = self.black_time if top_is_white else self.white_time

        top_active = (
            self.game_status not in GAME_OVER_STATUSES
            and TIME_CONTROLS.get(self.time_control_name) is not None
            and (self.white_turn == top_is_white)
        )
        bottom_active = (
            self.game_status not in GAME_OVER_STATUSES
            and TIME_CONTROLS.get(self.time_control_name) is not None
            and (self.white_turn != top_is_white)
        )

        self.top_clock_name.config(
            text=top_name,
            fg="#93C5FD" if top_active else THEME["muted"]
        )
        self.top_clock_time.config(
            text=format_clock_time(top_val),
            fg="#F87171" if (top_val is not None and top_val < 15.0) else (
                "#FFFFFF" if top_active else THEME["text"]
            )
        )
        self.bottom_clock_name.config(
            text=bottom_name,
            fg="#93C5FD" if bottom_active else THEME["muted"]
        )
        self.bottom_clock_time.config(
            text=format_clock_time(bottom_val),
            fg="#F87171" if (bottom_val is not None and bottom_val < 15.0) else (
                "#FFFFFF" if bottom_active else THEME["text"]
            )
        )

        top_caps = self.captured_by_white if top_is_white else self.captured_by_black
        bottom_caps = self.captured_by_black if top_is_white else self.captured_by_white
        self.top_captured_label.config(text=format_captured_tray(top_caps))
        self.bottom_captured_label.config(text=format_captured_tray(bottom_caps))

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        self.sound_button.config(text="🔊" if self.sound_enabled else "🔇")

    def export_pgn(self, save_dialog=True):
        white_name = (
            "Human"
            if (self.game_mode == MODE_PVP or self.human_color == HUMAN_COLOR_WHITE)
            else "Gambit AI"
        )
        black_name = (
            "Human"
            if (self.game_mode == MODE_PVP or self.human_color == HUMAN_COLOR_BLACK)
            else "Gambit AI"
        )
        pgn_text = build_pgn(
            self.san_history,
            self.game_status,
            self.white_turn,
            white_name=white_name,
            black_name=black_name,
            initial_fen=self.initial_fen,
        )
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(pgn_text)
        except Exception:
            pass

        if save_dialog and not self.closing:
            path = filedialog.asksaveasfilename(
                parent=self.root,
                title="Export Game as PGN",
                defaultextension=".pgn",
                filetypes=[("PGN Files", "*.pgn"), ("All Files", "*.*")],
                initialfile="gambit_game.pgn",
            )
            if path:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(pgn_text + "\n")
                messagebox.showinfo("PGN Exported", f"Saved PGN to {path}\n(Also copied to clipboard.)")
            else:
                messagebox.showinfo("PGN Copied", "PGN copied to clipboard.")
        return pgn_text

    def prompt_load_fen(self):
        if self.engine_busy or self.animating:
            return
        self._in_modal = True
        self._stop_clock()
        fen_result = {"value": None}
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title("Load FEN Position")
            dialog.resizable(False, False)
            dialog.configure(bg=THEME["sidebar"])
            dialog.transient(self.root)
            dialog.grab_set()

            tk.Label(
                dialog,
                text="Paste FEN Position",
                font=("Segoe UI", 13, "bold"),
                fg=THEME["text"],
                bg=THEME["sidebar"],
                padx=20
            ).pack(pady=(14, 6))

            entry = tk.Entry(
                dialog,
                width=62,
                font=("Consolas", 10),
                bg=THEME["list_bg"],
                fg=THEME["text"],
                insertbackground=THEME["text"],
                relief="flat",
                bd=6
            )
            entry.pack(padx=20, pady=(0, 10))
            entry.insert(0, self.initial_fen)
            entry.selection_range(0, tk.END)
            entry.focus_set()

            btn_row = tk.Frame(dialog, bg=THEME["sidebar"], padx=20)
            btn_row.pack(fill="x", pady=(0, 14))

            def on_ok():
                fen_result["value"] = entry.get().strip()
                dialog.destroy()

            tk.Button(
                btn_row,
                text="Load FEN",
                font=("Segoe UI", 10, "bold"),
                bg=THEME["accent_blue"],
                fg="#FFFFFF",
                relief="flat",
                bd=0,
                pady=6,
                padx=14,
                cursor="hand2",
                command=on_ok
            ).pack(side="left", expand=True, fill="x", padx=(0, 4))

            tk.Button(
                btn_row,
                text="Cancel",
                font=("Segoe UI", 10),
                bg=THEME["btn_bg"],
                fg=THEME["text"],
                relief="flat",
                bd=0,
                pady=6,
                padx=14,
                cursor="hand2",
                command=dialog.destroy
            ).pack(side="left", expand=True, fill="x", padx=(4, 0))

            dialog.bind("<Return>", lambda _e: on_ok())
            dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
            dialog.update_idletasks()
            x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
            y = self.root.winfo_rooty() + (self.root.winfo_height() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{max(0, x)}+{max(0, y)}")
            dialog.lift()
            self.root.wait_window(dialog)
        finally:
            self._in_modal = False

        if fen_result["value"]:
            self.load_fen(fen_result["value"])
        else:
            self._start_clock()

    def load_fen(self, fen_str):
        if self.engine_busy:
            return
        self._stop_clock()
        self.engine_busy = True
        self._update_controls()
        threading.Thread(
            target=self._process_load_fen,
            args=(fen_str,),
            daemon=True
        ).start()

    def _process_load_fen(self, fen_str):
        try:
            with self.engine_lock:
                ok = set_fen(self.engine, fen_str)
                if not ok:
                    raise ValueError(f"Invalid FEN string:\n{fen_str}")
                board, moves, status, turn = get_position(self.engine)
                engine_eval = get_engine_evaluation(self.engine)
                loaded_fen = get_fen(self.engine)

            if not self.closing:
                self.root.after(
                    0,
                    lambda: self._apply_loaded_fen(
                        board, moves, status, turn, engine_eval, loaded_fen
                    )
                )
        except Exception as e:
            if not self.closing:
                self.root.after(
                    0,
                    lambda err=str(e): self._handle_move_error("FEN Error", err)
                )

    def _apply_loaded_fen(self, board, moves, status, turn, engine_eval, loaded_fen):
        if self.closing:
            return
        self._cancel_animation()
        self.initial_fen = loaded_fen
        self.selected_square = None
        self.selected_moves = []
        self.last_move = None
        self.hint_move = None
        self.move_history = []
        self.san_history = []
        self.captured_by_white = []
        self.captured_by_black = []
        self.position_history = []
        self.view_index = -1
        self._reset_clocks(self.time_control_name)
        self.update_move_history()
        self.update_position(board, moves, status, turn, engine_eval=engine_eval)
        self._start_clock()
        if should_ai_move_for_turn(self.game_mode, status, turn, self.human_color):
            self.engine_busy = True
            self._update_controls()
            self.draw_board()
            threading.Thread(
                target=self.process_ai_turn,
                args=([r[:] for r in board], list(moves), status, turn),
                daemon=True
            ).start()

    def flip_board(self):
        if self.closing:
            return
        if self.animating:
            self._cancel_animation()
        self.board_flipped = not self.board_flipped
        self._refresh_clocks()
        self.draw_board()

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
        self._apply_game_config(
            mode,
            self.human_color,
            self.time_control_name
        )
        self._maybe_start_ai_opening()

    def choose_game_mode(self, allow_cancel=True):
        self._in_modal = True
        self._stop_clock()
        chosen = {"result": None}

        try:
            dialog = tk.Toplevel(self.root)
            dialog.title("New Game Setup")
            dialog.resizable(False, False)
            dialog.configure(bg=THEME["sidebar"])
            dialog.transient(self.root)
            dialog.grab_set()

            tk.Label(
                dialog,
                text="♟ Game Setup",
                font=("Segoe UI", 15, "bold"),
                fg=THEME["text"],
                bg=THEME["sidebar"],
                padx=24
            ).pack(pady=(16, 4))

            tk.Label(
                dialog,
                text=(
                    "Choose mode, your side (for PvAI), and time control."
                ),
                font=("Segoe UI", 10),
                fg=THEME["muted"],
                bg=THEME["sidebar"],
                justify="center",
                padx=24
            ).pack(pady=(0, 10))

            options_frame = tk.Frame(dialog, bg=THEME["card"], padx=14, pady=10)
            options_frame.pack(fill="x", padx=24, pady=(0, 10))

            # Side selection for PvAI
            side_row = tk.Frame(options_frame, bg=THEME["card"])
            side_row.pack(fill="x", pady=(0, 8))
            tk.Label(
                side_row,
                text="Play As (PvAI):",
                font=("Segoe UI", 10, "bold"),
                fg=THEME["text"],
                bg=THEME["card"]
            ).pack(side="left")

            side_var = tk.StringVar(
                value="White" if self.human_color == HUMAN_COLOR_WHITE else "Black"
            )
            side_menu = tk.OptionMenu(side_row, side_var, "White", "Black", "Random")
            side_menu.config(
                font=("Segoe UI", 10),
                bg=THEME["btn_bg"],
                fg=THEME["text"],
                activebackground=THEME["btn_active"],
                activeforeground="#FFFFFF",
                highlightthickness=0,
                bd=0
            )
            side_menu["menu"].config(
                bg=THEME["card"],
                fg=THEME["text"],
                activebackground=THEME["accent_blue"],
                activeforeground="#FFFFFF"
            )
            side_menu.pack(side="right")

            # Time control selection
            clock_row = tk.Frame(options_frame, bg=THEME["card"])
            clock_row.pack(fill="x")
            tk.Label(
                clock_row,
                text="Time Control:",
                font=("Segoe UI", 10, "bold"),
                fg=THEME["text"],
                bg=THEME["card"]
            ).pack(side="left")

            clock_var = tk.StringVar(value=self.time_control_name)
            clock_menu = tk.OptionMenu(clock_row, clock_var, *TIME_CONTROLS.keys())
            clock_menu.config(
                font=("Segoe UI", 10),
                bg=THEME["btn_bg"],
                fg=THEME["text"],
                activebackground=THEME["btn_active"],
                activeforeground="#FFFFFF",
                highlightthickness=0,
                bd=0
            )
            clock_menu["menu"].config(
                bg=THEME["card"],
                fg=THEME["text"],
                activebackground=THEME["accent_blue"],
                activeforeground="#FFFFFF"
            )
            clock_menu.pack(side="right")

            btn_frame = tk.Frame(dialog, bg=THEME["sidebar"], padx=24, pady=8)
            btn_frame.pack(fill="x")

            def select(mode):
                side_choice = side_var.get()
                if side_choice == "Random":
                    resolved_color = random.choice(
                        (HUMAN_COLOR_WHITE, HUMAN_COLOR_BLACK)
                    )
                elif side_choice == "Black":
                    resolved_color = HUMAN_COLOR_BLACK
                else:
                    resolved_color = HUMAN_COLOR_WHITE
                chosen["result"] = (mode, resolved_color, clock_var.get())
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

            def on_close():
                if not allow_cancel and chosen["result"] is None:
                    chosen["result"] = (
                        self.game_mode,
                        self.human_color,
                        self.time_control_name,
                    )
                dialog.destroy()

            dialog.protocol("WM_DELETE_WINDOW", on_close)
            dialog.update_idletasks()
            x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
            y = self.root.winfo_rooty() + (self.root.winfo_height() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{max(0, x)}+{max(0, y)}")
            dialog.lift()
            dialog.focus_force()

            self.root.wait_window(dialog)
        finally:
            self._in_modal = False

        return chosen["result"]

    def get_ai_depth(self):
        return AI_DIFFICULTY_DEPTHS.get(self.difficulty_var.get(), 4)

    def get_ai_time_limit(self):
        return AI_DIFFICULTY_TIME_LIMITS.get(self.difficulty_var.get(), 1.5)

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
        self.time_menu.config(state=state)
        self.fen_button.config(state=state)
        ai_state = (
            "normal"
            if (not self.engine_busy and self.game_mode == MODE_PVAI)
            else "disabled"
        )
        self.difficulty_menu.config(state=ai_state)
        self.side_menu.config(state=ai_state)

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
        can_draw = can_resign and (self.game_mode == MODE_PVP)
        self.draw_button.config(
            state="normal" if can_draw else "disabled"
        )
        can_hint = (
            not self.engine_busy
            and not self.animating
            and bool(self.board)
            and self.is_viewing_live()
            and self.game_status not in GAME_OVER_STATUSES
        )
        self.hint_button.config(
            state="normal" if can_hint else "disabled"
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
        appended_san=None,
        captured_piece=None,
        keep_busy=False,
        engine_eval=None,
        animate_from=None
    ):
        if self.closing:
            return

        self._cancel_animation()
        self.hint_move = None
        self.board = [row[:] for row in board]
        self.legal_moves = moves
        self.game_status = status
        self.white_turn = turn == "WHITE"
        if last_move is not None:
            self.last_move = last_move
        if appended_move is not None:
            self.move_history.append(appended_move)
            self.san_history.append(appended_san or appended_move)
            if captured_piece is not None:
                if captured_piece.islower():
                    self.captured_by_white.append(captured_piece)
                else:
                    self.captured_by_black.append(captured_piece)

        snapshot = {
            "board": [row[:] for row in board],
            "status": status,
            "white_turn": (turn == "WHITE"),
            "last_move": self.last_move,
            "engine_eval": self.engine_eval if engine_eval is None else engine_eval,
            "captured_by_white": list(self.captured_by_white),
            "captured_by_black": list(self.captured_by_black),
        }
        if appended_move is not None or not self.position_history:
            self.position_history.append(snapshot)
        else:
            self.position_history[-1] = snapshot
        self.view_index = len(self.position_history) - 1

        if appended_move is not None:
            self.update_move_history()
            moved_white = (turn != "WHITE")
            self._apply_increment(moved_white)
            if self._clock_last_tick is not None:
                self._clock_last_tick = time.monotonic()

            if status in GAME_OVER_STATUSES:
                play_sound("gameover", self.sound_enabled)
            elif status == "CHECK":
                play_sound("check", self.sound_enabled)
            elif (appended_san or "").startswith("O-O"):
                play_sound("castle", self.sound_enabled)
            elif captured_piece is not None:
                play_sound("capture", self.sound_enabled)
            else:
                play_sound("move", self.sound_enabled)

        self.engine_busy = keep_busy

        if self.game_status in GAME_OVER_STATUSES:
            self._stop_clock()

        self.update_evaluation_panel(board, engine_eval=engine_eval)
        self._refresh_clocks()
        self._update_controls()

        if (
            animate_from is not None
            and len(animate_from) == 2
            and self.canvas.winfo_width() > 20
        ):
            from_sq, to_sq = animate_from
            to_r, to_c = notation_to_coords(to_sq)
            moving_piece = self.board[to_r][to_c]
            if moving_piece not in (".", " "):
                self._animate_move_step(
                    self.view_index,
                    self.board,
                    moving_piece,
                    from_sq,
                    to_sq,
                    total_steps=6,
                    frame_ms=12,
                )
                return

        self.draw_board()

    # ---------------- MOVE SELECTION & DRAG-DROP ----------------

    def _event_to_board_square(self, event):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        _, square_size, offset_x, offset_y = get_board_geometry(width, height)
        if square_size <= 0:
            return None

        disp_col = int((event.x - offset_x) / square_size)
        disp_row = int((event.y - offset_y) / square_size)

        if disp_row < 0 or disp_row >= 8 or disp_col < 0 or disp_col >= 8:
            return None

        row, col = display_to_board_coords(disp_row, disp_col, self.board_flipped)
        return row, col, self.square_to_notation(row, col)

    def _can_interact_now(self):
        if self.engine_busy:
            return False
        if self.animating:
            self._cancel_animation()
        return (
            self.is_viewing_live()
            and self.game_status not in GAME_OVER_STATUSES
            and can_human_interact(self.game_mode, self.white_turn, self.human_color)
            and bool(self.board)
        )

    def _handle_square_click(self, clicked_square, row, col):
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
            return

        same_destination = [
            move for move in self.selected_moves
            if move[2:4] == clicked_square
        ]

        if same_destination:
            move_found = same_destination[0]
            if any(len(move) >= 5 for move in same_destination):
                move_found = self.choose_promotion(same_destination)
                if move_found is None:
                    return

            self.selected_square = None
            self.selected_moves = []
            self.make_move(move_found, animate=True)
            return

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

    def on_click(self, event):
        if not self._can_interact_now():
            return
        coords = self._event_to_board_square(event)
        if coords is None:
            return
        row, col, clicked_square = coords
        self._handle_square_click(clicked_square, row, col)

    def on_mouse_down(self, event):
        self._drag_state = None
        if not self._can_interact_now():
            return
        coords = self._event_to_board_square(event)
        if coords is None:
            return
        row, col, clicked_square = coords
        piece = self.board[row][col]

        if is_own_piece(piece, self.white_turn):
            moves = [
                move for move in self.legal_moves
                if move[:2] == clicked_square
            ]
            self._drag_state = {
                "from_sq": clicked_square,
                "piece": piece,
                "moves": moves,
                "start_x": event.x,
                "start_y": event.y,
                "dragging": False,
            }
            if moves:
                self.selected_square = clicked_square
                self.selected_moves = moves
            else:
                self.selected_square = None
                self.selected_moves = []
            self.draw_board()
            return

        self._handle_square_click(clicked_square, row, col)

    def on_mouse_drag(self, event):
        state = self._drag_state
        if not state or not state["moves"] or self.engine_busy or self.animating:
            return

        if not state["dragging"]:
            if abs(event.x - state["start_x"]) + abs(event.y - state["start_y"]) < 6:
                return
            state["dragging"] = True

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        _, square_size, _, _ = get_board_geometry(width, height)
        self.draw_board(hidden_square=state["from_sq"])
        self.draw_piece(state["piece"], event.x, event.y, square_size)

    def on_mouse_up(self, event):
        state = self._drag_state
        self._drag_state = None
        if not state or not state["dragging"]:
            return

        coords = self._event_to_board_square(event)
        if coords is None:
            self.draw_board()
            return

        _, _, target_square = coords
        same_destination = [
            move for move in state["moves"]
            if move[2:4] == target_square
        ]
        if not same_destination:
            if target_square != state["from_sq"]:
                self.selected_square = None
                self.selected_moves = []
            self.draw_board()
            return

        move_found = same_destination[0]
        if any(len(move) >= 5 for move in same_destination):
            self.draw_board()
            move_found = self.choose_promotion(same_destination)
            if move_found is None:
                return

        self.selected_square = None
        self.selected_moves = []
        self.make_move(move_found, animate=False)

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
            padx=18
        ).pack(pady=(14, 6))

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

    def make_move(self, move, animate=True):

        if self.engine_busy:
            return
        if self.animating:
            self._cancel_animation()

        if (
            not self.is_viewing_live()
            or self.game_status in GAME_OVER_STATUSES
        ):
            return

        board_before = [row[:] for row in self.board]
        moves_before = list(self.legal_moves)
        self.engine_busy = True
        self.hint_move = None
        self._update_controls()
        self.draw_board()

        threading.Thread(
            target=self.process_human_move,
            args=(move, board_before, moves_before, animate),
            daemon=True
        ).start()

    def process_human_move(self, move, board_before=None, moves_before=None, animate=True):

        try:
            if board_before is None:
                board_before = [row[:] for row in self.board]
            if moves_before is None:
                moves_before = list(self.legal_moves)

            captured_piece = get_captured_piece(board_before, move)

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

            san_text = format_san_move(
                board_before,
                moves_before,
                move,
                next_status=status
            )

            should_ai_move = should_ai_move_for_turn(
                self.game_mode, status, turn, self.human_color
            )
            anim_pair = (move[:2], move[2:4]) if (animate and len(move) >= 4) else None

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
                        appended_san=san_text,
                        captured_piece=captured_piece,
                        keep_busy=should_ai_move,
                        engine_eval=engine_eval,
                        animate_from=anim_pair
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

            board_before = [row[:] for row in board]
            moves_before = list(moves)
            depth = self.get_ai_depth()
            time_limit = self.get_ai_time_limit()
            time_limit_ms = max(100, int(time_limit * 1000))

            with self.engine_lock:
                ai_move, _, _ = get_cpp_best_move(
                    self.engine,
                    depth=depth,
                    time_limit_ms=time_limit_ms
                )

                if ai_move is None and moves_before:
                    ai_move = self.ai.find_best_move(
                        board_before,
                        moves_before,
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

                captured_piece = get_captured_piece(board_before, ai_move)
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

            san_text = format_san_move(
                board_before,
                moves_before,
                ai_move,
                next_status=status
            )
            anim_pair = (ai_move[:2], ai_move[2:4]) if len(ai_move) >= 4 else None

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
                        appended_san=san_text,
                        captured_piece=captured_piece,
                        keep_busy=False,
                        engine_eval=engine_eval,
                        animate_from=anim_pair
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

        self._stop_clock()
        self.selected_square = None
        self.selected_moves = []
        self.hint_move = None
        self.game_status = (
            "RESIGNED_WHITE" if self.white_turn else "RESIGNED_BLACK"
        )
        if self.position_history:
            self.position_history[-1]["status"] = self.game_status
        play_sound("gameover", self.sound_enabled)
        self._refresh_clocks()
        self._update_controls()
        self.draw_board()

    def offer_draw(self, confirm=True):
        if (
            self.engine_busy
            or self.animating
            or not self.board
            or not self.is_viewing_live()
            or self.game_status in GAME_OVER_STATUSES
            or self.game_mode != MODE_PVP
        ):
            return

        if confirm:
            side = "White" if self.white_turn else "Black"
            opponent = "Black" if self.white_turn else "White"
            ok = messagebox.askyesno(
                "Offer Draw",
                f"{side} offers a draw.\nDoes {opponent} accept the draw?"
            )
            if not ok:
                return

        self._stop_clock()
        self.selected_square = None
        self.selected_moves = []
        self.hint_move = None
        self.game_status = "DRAW_AGREED"
        if self.position_history:
            self.position_history[-1]["status"] = self.game_status
        play_sound("gameover", self.sound_enabled)
        self._refresh_clocks()
        self._update_controls()
        self.draw_board()

    def request_hint(self):
        if (
            self.engine_busy
            or self.animating
            or not self.board
            or not self.is_viewing_live()
            or self.game_status in GAME_OVER_STATUSES
        ):
            return

        self.engine_busy = True
        self._update_controls()
        threading.Thread(
            target=self._process_hint,
            daemon=True
        ).start()

    def _process_hint(self):
        try:
            with self.engine_lock:
                hint_move, _, _ = get_cpp_best_move(
                    self.engine,
                    depth=4,
                    time_limit_ms=900
                )
            if not self.closing:
                self.root.after(
                    0,
                    lambda m=hint_move: self._apply_hint(m)
                )
        except Exception:
            if not self.closing:
                self.root.after(
                    0,
                    lambda: self._apply_hint(None)
                )

    def _apply_hint(self, hint_move):
        if self.closing:
            return
        self.engine_busy = False
        self.hint_move = hint_move
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
        self.captured_by_white = list(snapshot.get("captured_by_white", []))
        self.captured_by_black = list(snapshot.get("captured_by_black", []))
        self.hint_move = None
        self.selected_square = None
        self.selected_moves = []

        self.update_evaluation_panel(
            self.board,
            engine_eval=snapshot["engine_eval"]
        )
        self._refresh_clocks()
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
        total_steps=8,
        frame_ms=15
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
        disp_from_r, disp_from_c = board_to_display_coords(
            from_r, from_c, self.board_flipped
        )
        disp_to_r, disp_to_c = board_to_display_coords(
            to_r, to_c, self.board_flipped
        )
        x_start = offset_x + (disp_from_c + 0.5) * square_size
        y_start = offset_y + (disp_from_r + 0.5) * square_size
        x_end = offset_x + (disp_to_c + 0.5) * square_size
        y_end = offset_y + (disp_to_r + 0.5) * square_size

        t = step / total_steps
        ease = 1.0 - (1.0 - t) ** 2
        cur_x = x_start + (x_end - x_start) * ease
        cur_y = y_start + (y_end - y_start) * ease

        if moving_piece not in (".", " "):
            self.draw_piece(moving_piece, cur_x, cur_y, square_size)

        self._anim_after_id = self.root.after(
            frame_ms,
            lambda: self._animate_move_step(
                target_index,
                target_board,
                moving_piece,
                from_sq,
                to_sq,
                step=step + 1,
                total_steps=total_steps,
                frame_ms=frame_ms
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

    def new_game(
        self,
        mode=None,
        prompt_mode=None,
        human_color=None,
        time_control=None
    ):

        if self.engine_busy:
            return

        selected_mode = self.game_mode
        selected_color = self.human_color
        selected_clock = self.time_control_name

        if (
            mode in GAME_MODE_LABELS
            or human_color in (HUMAN_COLOR_WHITE, HUMAN_COLOR_BLACK)
            or time_control in TIME_CONTROLS
        ):
            if mode in GAME_MODE_LABELS:
                selected_mode = mode
            if human_color in (HUMAN_COLOR_WHITE, HUMAN_COLOR_BLACK):
                selected_color = human_color
            if time_control in TIME_CONTROLS:
                selected_clock = time_control
        elif prompt_mode is True or (prompt_mode is None and self.prompt_mode_on_start):
            config = self.choose_game_mode(allow_cancel=True)
            if config is None:
                self._start_clock()
                return
            selected_mode, selected_color, selected_clock = config

        self._stop_clock()
        self.engine_busy = True
        self._update_controls()

        threading.Thread(
            target=self.send_new_game,
            args=((selected_mode, selected_color, selected_clock),),
            daemon=True
        ).start()

    def send_new_game(self, selected_config=None):

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
                        board, moves, status, turn, engine_eval, selected_config
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
        selected_config=None
    ):
        if self.closing:
            return

        if isinstance(selected_config, tuple) and len(selected_config) == 3:
            mode, color, clock_name = selected_config
            self._apply_game_config(mode, color, clock_name)
            self._reset_clocks(clock_name)
        else:
            if selected_config in GAME_MODE_LABELS:
                self._apply_game_config(
                    selected_config,
                    self.human_color,
                    self.time_control_name
                )
            self._reset_clocks(self.time_control_name)

        self._cancel_animation()
        self.selected_square = None
        self.selected_moves = []
        self.last_move = None
        self.hint_move = None
        self.move_history = []
        self.san_history = []
        self.captured_by_white = []
        self.captured_by_black = []
        self.initial_fen = STANDARD_START_FEN
        self.position_history = []
        self.view_index = -1
        self.update_move_history()
        self.update_position(board, moves, status, turn, engine_eval=engine_eval)
        self._start_clock()
        self._maybe_start_ai_opening()

    # ---------------- MOVE HISTORY ----------------

    def update_move_history(self):

        self.history_list.delete(
            0, tk.END
        )

        display_moves = (
            self.san_history
            if len(self.san_history) == len(self.move_history)
            else self.move_history
        )

        for i in range(0, len(display_moves), 2):

            move_number = (i // 2) + 1
            white_move = display_moves[i]

            if i + 1 < len(display_moves):

                black_move = display_moves[i + 1]

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
                game_mode=self.game_mode,
                human_color=self.human_color
            )

        self.canvas.create_text(
            width / 2,
            22,
            text=turn_text,
            font=("Segoe UI", 14, "bold"),
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

                disp_row, disp_col = board_to_display_coords(
                    row, col, self.board_flipped
                )
                x1 = offset_x + disp_col * square_size
                y1 = offset_y + disp_row * square_size
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

                if disp_col == 0:

                    self.canvas.create_text(
                        x1 + 6,
                        y1 + 5,
                        text=str(8 - row),
                        anchor="nw",
                        font=("Segoe UI", 10, "bold"),
                        fill=dark if is_light else light
                    )

                if disp_row == 7:

                    self.canvas.create_text(
                        x2 - 6,
                        y2 - 4,
                        text=chr(ord("a") + col),
                        anchor="se",
                        font=("Segoe UI", 10, "bold"),
                        fill=dark if is_light else light
                    )

        if (
            self.hint_move
            and len(self.hint_move) >= 4
            and viewing_live
        ):
            from_r, from_c = notation_to_coords(self.hint_move[:2])
            to_r, to_c = notation_to_coords(self.hint_move[2:4])
            disp_from_r, disp_from_c = board_to_display_coords(
                from_r, from_c, self.board_flipped
            )
            disp_to_r, disp_to_c = board_to_display_coords(
                to_r, to_c, self.board_flipped
            )
            hx1 = offset_x + (disp_from_c + 0.5) * square_size
            hy1 = offset_y + (disp_from_r + 0.5) * square_size
            hx2 = offset_x + (disp_to_c + 0.5) * square_size
            hy2 = offset_y + (disp_to_r + 0.5) * square_size
            arrow_w = max(4, int(square_size * 0.12))
            self.canvas.create_line(
                hx1,
                hy1,
                hx2,
                hy2,
                fill="#F59E0B",
                width=arrow_w,
                arrow=tk.LAST,
                arrowshape=(
                    max(12, int(square_size * 0.24)),
                    max(15, int(square_size * 0.28)),
                    max(5, int(square_size * 0.10)),
                ),
                capstyle=tk.ROUND,
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
        self._stop_clock()
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
