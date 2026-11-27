
import os
import random
import subprocess
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox

from ai import (
    AI,
    analyze_position_with_engine,
    get_cpp_best_move,
    get_engine_evaluation,
    get_fen,
    get_position,
    send_move_to_engine,
    set_fen,
)
from chess_utils import (
    DEFAULT_APP_ICON_PATH,
    DEFAULT_SETTINGS_PATH,
    DEFAULT_TIME_CONTROLS,
    STANDARD_START_FEN,
    build_pgn,
    calculate_accuracy,
    classify_cp_loss,
    detect_opening_name,
    format_captured_tray,
    format_san_move,
    generate_app_icon,
    get_captured_piece,
    load_user_settings,
    parse_custom_time_control,
    play_sound,
    resolve_time_control_spec,
    save_user_settings,
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

TIME_CONTROLS = dict(DEFAULT_TIME_CONTROLS)

SETTINGS_AUTO = "__AUTO__"

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
    "bg": "#0D1012",
    "sidebar": "#15191D",
    "card": "#1D2329",
    "border": "#2B333C",
    "text": "#F3F4F6",
    "muted": "#9CA3AF",
    "accent_blue": "#0D9488",
    "accent_primary_hover": "#0F766E",
    "accent_soft": "#5EEAD4",
    "accent_badge_bg": "#113832",
    "accent_badge_fg": "#2DD4BF",
    "accent_green": "#059669",
    "accent_red": "#DC2626",
    "btn_bg": "#262D35",
    "btn_active": "#323B46",
    "list_bg": "#101417",
    "graph_top": "#1B2228",
    "graph_bottom": "#0F1316",
}

BOARD_THEMES = {
    "Classic Green": {
        "light": "#EEEED2",
        "dark": "#769656",
        "selected": "#F6F669",
        "last_light": "#F5F682",
        "last_dark": "#BACA44",
        "check": "#E05252",
        "dot_light": "#7B9361",
        "dot_dark": "#4A6B35",
        "ring": "#3D5A2A",
    },
    "Walnut Wood": {
        "light": "#F0D9B5",
        "dark": "#B58863",
        "selected": "#F6E58D",
        "last_light": "#E6D27A",
        "last_dark": "#C2A14D",
        "check": "#E05252",
        "dot_light": "#A58A68",
        "dot_dark": "#7B573B",
        "ring": "#6D4C32",
    },
    "Slate Blue": {
        "light": "#DEE3E6",
        "dark": "#8CA2AD",
        "selected": "#93C5FD",
        "last_light": "#BAE6FD",
        "last_dark": "#6B9EC2",
        "check": "#E05252",
        "dot_light": "#7690A0",
        "dot_dark": "#526B7A",
        "ring": "#3E5664",
    },
    "Tournament Charcoal": {
        "light": "#DCDCDC",
        "dark": "#6E7887",
        "selected": "#FDE047",
        "last_light": "#E5E79D",
        "last_dark": "#9CA85E",
        "check": "#E05252",
        "dot_light": "#848C98",
        "dot_dark": "#4B5563",
        "ring": "#374151",
    },
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
        time_control=None,
        settings_path=SETTINGS_AUTO
    ):
        self.root = root
        self.root.title("Gambit Chess")
        self.root.minsize(880, 620)
        self.root.configure(bg=THEME["bg"])

        try:
            if not os.path.exists(DEFAULT_APP_ICON_PATH):
                generate_app_icon(DEFAULT_APP_ICON_PATH)
            if os.path.exists(DEFAULT_APP_ICON_PATH):
                self.root.iconbitmap(DEFAULT_APP_ICON_PATH)
        except Exception:
            pass

        if settings_path == SETTINGS_AUTO:
            self.settings_path = DEFAULT_SETTINGS_PATH if prompt_mode_on_start else None
        else:
            self.settings_path = settings_path

        saved_prefs = (
            load_user_settings(self.settings_path)
            if self.settings_path
            else {}
        )

        self.engine = self._spawn_engine_process()
        self.ai = AI(self.engine)

        self.prompt_mode_on_start = prompt_mode_on_start
        pref_mode = saved_prefs.get("game_mode")
        if game_mode in GAME_MODE_LABELS:
            self.game_mode = game_mode
        elif pref_mode in GAME_MODE_LABELS:
            self.game_mode = pref_mode
        else:
            self.game_mode = MODE_PVAI

        pref_color = saved_prefs.get("human_color")
        if human_color in (HUMAN_COLOR_WHITE, HUMAN_COLOR_BLACK) and (
            game_mode is not None or not self.settings_path or pref_color not in (HUMAN_COLOR_WHITE, HUMAN_COLOR_BLACK)
        ):
            self.human_color = human_color
        elif pref_color in (HUMAN_COLOR_WHITE, HUMAN_COLOR_BLACK):
            self.human_color = pref_color
        else:
            self.human_color = HUMAN_COLOR_WHITE

        self.board_flipped = (
            self.game_mode == MODE_PVAI
            and self.human_color == HUMAN_COLOR_BLACK
        )

        chosen_tc = time_control if time_control is not None else saved_prefs.get("time_control", "Untimed")
        resolved_spec = resolve_time_control_spec(chosen_tc)
        if chosen_tc not in TIME_CONTROLS and resolved_spec is not None:
            TIME_CONTROLS[chosen_tc] = resolved_spec
        self.time_control_name = chosen_tc if chosen_tc in TIME_CONTROLS else "Untimed"
        self.white_time = None
        self.black_time = None
        self._clock_last_tick = None
        self._clock_after_id = None
        self._in_modal = False

        self.engine_eval = 0
        self.ai_eval_cp = 0
        self.current_eval_score = 0.0

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
        self._right_drag_start = None
        self.user_arrows = []
        self.highlighted_squares = set()
        self.premove = None
        self._premove_selected = None
        pref_theme = saved_prefs.get("board_theme")
        self.board_theme_name = pref_theme if pref_theme in BOARD_THEMES else "Classic Green"
        self.eval_history = []
        self.opening_name = "Starting Position"
        self.review_annotations = []
        self.review_summary = None
        self.review_busy = False
        self.review_best_move = None
        self.hint_move = None
        if "sound_enabled" in saved_prefs:
            self.sound_enabled = bool(saved_prefs["sound_enabled"])
        else:
            self.sound_enabled = bool(prompt_mode_on_start)
        pref_diff = saved_prefs.get("difficulty")
        self._initial_difficulty = (
            pref_diff if pref_diff in AI_DIFFICULTY_DEPTHS else "Medium (Depth 4)"
        )
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
        self.canvas.pack(side="left", fill="both", expand=True, padx=(14, 10), pady=12)

        self.history_frame = tk.Frame(
            self.main_frame,
            width=386,
            bg=THEME["sidebar"],
            highlightthickness=1,
            highlightbackground=THEME["border"]
        )
        self.history_frame.pack(side="right", fill="y", padx=(0, 14), pady=12)
        self.history_frame.pack_propagate(False)

        # ---- Header & Mode Selector ----
        self.header_frame = tk.Frame(self.history_frame, bg=THEME["sidebar"])
        self.header_frame.pack(fill="x", padx=16, pady=(8, 5))

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

        self.theme_var = tk.StringVar(value=self.board_theme_name)
        self.theme_button = tk.Menubutton(
            self.title_row,
            text="🎨",
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
            direction="below"
        )
        self.theme_menu = tk.Menu(
            self.theme_button,
            tearoff=0,
            bg=THEME["card"],
            fg=THEME["text"],
            activebackground=THEME["accent_blue"],
            activeforeground="#FFFFFF"
        )
        for theme_name in BOARD_THEMES:
            self.theme_menu.add_radiobutton(
                label=theme_name,
                variable=self.theme_var,
                value=theme_name,
                command=lambda t=theme_name: self.set_board_theme(t)
            )
        self.theme_button.config(menu=self.theme_menu)
        self.theme_button.pack(side="right", padx=(0, 3))

        self.mode_label = tk.Label(
            self.header_frame,
            text=f"Mode: {GAME_MODE_LABELS[self.game_mode]}",
            font=("Segoe UI", 9, "bold"),
            fg=THEME["accent_soft"],
            bg=THEME["sidebar"],
            anchor="w"
        )
        self.mode_label.pack(fill="x", pady=(1, 5))

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
        self.pvai_mode_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

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
        self.pvp_mode_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # ---- Clocks Card ----
        self.clock_frame = tk.Frame(
            self.history_frame,
            bg=THEME["card"],
            highlightthickness=1,
            highlightbackground=THEME["border"],
            padx=8,
            pady=5
        )
        self.clock_frame.pack(fill="x", padx=16, pady=(0, 6))

        self.top_clock_box = tk.Frame(self.clock_frame, bg=THEME["list_bg"], padx=10, pady=3)
        self.top_clock_box.pack(side="left", fill="x", expand=True, padx=(0, 4))

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

        self.bottom_clock_box = tk.Frame(self.clock_frame, bg=THEME["list_bg"], padx=10, pady=3)
        self.bottom_clock_box.pack(side="left", fill="x", expand=True, padx=(4, 0))

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
        self.eval_frame = tk.Frame(
            self.history_frame,
            bg=THEME["card"],
            highlightthickness=1,
            highlightbackground=THEME["border"],
            padx=12,
            pady=7
        )
        self.eval_frame.pack(fill="x", padx=16, pady=(0, 6))

        self.eval_header_row = tk.Frame(self.eval_frame, bg=THEME["card"])
        self.eval_header_row.pack(fill="x")

        tk.Label(
            self.eval_header_row,
            text="POSITION EVALUATION",
            font=("Segoe UI", 8, "bold"),
            fg=THEME["muted"],
            bg=THEME["card"],
            anchor="w"
        ).pack(side="left")

        self.eval_live_badge = tk.Label(
            self.eval_header_row,
            text="AI+ LIVE",
            font=("Segoe UI", 7, "bold"),
            fg=THEME["accent_badge_fg"],
            bg=THEME["accent_badge_bg"],
            padx=6,
            pady=1
        )
        self.eval_live_badge.pack(side="right")

        self.eval_headline_label = tk.Label(
            self.eval_frame,
            text="Position is equal: 0.0",
            font=("Segoe UI", 11, "bold"),
            fg=THEME["text"],
            bg=THEME["card"],
            anchor="w"
        )
        self.eval_headline_label.pack(fill="x", pady=(2, 4))

        self.eval_bar = tk.Canvas(
            self.eval_frame,
            height=9,
            bg=THEME["list_bg"],
            highlightthickness=0
        )
        self.eval_bar.pack(fill="x", pady=(0, 3))
        self.eval_bar.bind("<Configure>", lambda _e: self._draw_eval_bar(self.current_eval_score))
        self.current_material_score = 0

        self.eval_graph = tk.Canvas(
            self.eval_frame,
            height=22,
            bg=THEME["list_bg"],
            highlightthickness=0,
            cursor="hand2"
        )
        self.eval_graph.pack(fill="x", pady=(0, 5))
        self.eval_graph.bind("<Configure>", lambda _e: self._draw_eval_graph())
        self.eval_graph.bind("<Button-1>", self.on_eval_graph_click)

        self.ai_eval_label = tk.Label(
            self.eval_frame,
            text="AI Positional Eval (Search AI+): 0.00",
            font=("Segoe UI", 9, "bold"),
            fg="#E2E8F0",
            bg=THEME["card"],
            anchor="w"
        )
        self.ai_eval_label.pack(fill="x", pady=(0, 1))

        self.engine_eval_label = tk.Label(
            self.eval_frame,
            text="C++ Engine Eval (material-only): 0.0",
            font=("Segoe UI", 8),
            fg=THEME["muted"],
            bg=THEME["card"],
            anchor="w"
        )
        self.engine_eval_label.pack(fill="x", pady=(0, 4))

        self.material_row = tk.Frame(self.eval_frame, bg=THEME["card"])
        self.material_row.pack(fill="x")

        self.white_material_label = tk.Label(
            self.material_row,
            text="W: Q1 R2 B2 N2 P8",
            font=("Consolas", 8),
            fg="#F9FAFB",
            bg=THEME["card"],
            anchor="w"
        )
        self.white_material_label.pack(side="left")

        self.black_material_label = tk.Label(
            self.material_row,
            text="B: q1 r2 b2 n2 p8",
            font=("Consolas", 8),
            fg="#CBD5E1",
            bg=THEME["card"],
            anchor="e"
        )
        self.black_material_label.pack(side="right")

        self.material_diff_label = tk.Label(
            self.eval_frame,
            text="Material is equal. (0.0 pts)",
            font=("Segoe UI", 8),
            fg=THEME["accent_soft"],
            bg=THEME["card"],
            anchor="w",
            justify="left",
            wraplength=330
        )
        self.material_diff_label.pack(fill="x", pady=(3, 0))

        # ---- Bottom Controls (packed bottom-first so always visible!) ----
        self.action_frame = tk.Frame(self.history_frame, bg=THEME["sidebar"])
        self.action_frame.pack(side="bottom", fill="x", padx=16, pady=(0, 10))

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
            activebackground=THEME["accent_primary_hover"],
            activeforeground="#FFFFFF",
            disabledforeground="#99F6E4",
            relief="flat",
            bd=0,
            pady=7,
            cursor="hand2",
            command=self.new_game
        )
        self.new_game_button.pack(side="left", fill="x", expand=True, padx=(3, 0))

        self.review_frame = tk.Frame(self.history_frame, bg=THEME["sidebar"])
        self.review_frame.pack(side="bottom", fill="x", padx=16, pady=(0, 5))

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
        self.settings_frame.pack(side="bottom", fill="x", padx=16, pady=(0, 5))

        self.options_row = tk.Frame(self.settings_frame, bg=THEME["sidebar"])
        self.options_row.pack(fill="x", pady=(0, 4))

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
            "Custom...",
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

        self.difficulty_var = tk.StringVar(value=self._initial_difficulty)
        self.difficulty_menu = tk.OptionMenu(
            self.difficulty_frame,
            self.difficulty_var,
            *AI_DIFFICULTY_DEPTHS.keys(),
            command=self.on_sidebar_difficulty_change
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

        # ---- Move History & Opening / Review Header ----
        self.history_header_frame = tk.Frame(self.history_frame, bg=THEME["sidebar"])
        self.history_header_frame.pack(fill="x", padx=16, pady=(0, 2))

        self.history_title = tk.Label(
            self.history_header_frame,
            text="Move History",
            font=("Segoe UI", 10, "bold"),
            fg=THEME["muted"],
            bg=THEME["sidebar"],
            anchor="w"
        )
        self.history_title.pack(side="left")

        self.review_game_button = tk.Button(
            self.history_header_frame,
            text="🔍 Review",
            font=("Segoe UI", 8, "bold"),
            bg=THEME["btn_bg"],
            fg=THEME["accent_badge_fg"],
            activebackground=THEME["btn_active"],
            activeforeground="#99F6E4",
            disabledforeground="#6B7280",
            relief="flat",
            bd=0,
            padx=6,
            pady=1,
            cursor="hand2",
            command=self.review_game,
            state="disabled"
        )
        self.review_game_button.pack(side="right")

        self.opening_label = tk.Label(
            self.history_frame,
            text="Opening: Starting Position",
            font=("Segoe UI", 8, "bold"),
            fg=THEME["accent_soft"],
            bg=THEME["sidebar"],
            anchor="w"
        )
        self.opening_label.pack(fill="x", padx=16, pady=(0, 4))

        self.history_list_frame = tk.Frame(
            self.history_frame,
            bg=THEME["list_bg"],
            highlightthickness=1,
            highlightbackground=THEME["border"]
        )
        self.history_list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 6))

        self.history_scroll = tk.Scrollbar(self.history_list_frame)
        self.history_scroll.pack(side="right", fill="y")

        self.history_list = tk.Listbox(
            self.history_list_frame,
            height=3,
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
        self.canvas.bind("<ButtonPress-3>", self.on_right_down)
        self.canvas.bind("<ButtonRelease-3>", self.on_right_up)
        self.history_list.bind("<ButtonRelease-1>", self.on_history_click)
        self._bind_shortcuts()

        self._reset_clocks(self.time_control_name)
        self._refresh_mode_buttons()
        self.root.state("zoomed")

        self.root.after(100, self.initial_position)

    # ---------------- ENGINE POSITION ----------------

    def _spawn_engine_process(self):
        engine_dir = os.path.dirname(os.path.abspath(__file__))
        engine_path = os.path.join(engine_dir, "gambit.exe")
        if not os.path.exists(engine_path):
            engine_path = "gambit.exe"
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        return subprocess.Popen(
            [engine_path],
            cwd=engine_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
            creationflags=creation_flags,
        )

    def _close_engine_pipes(self, proc):
        if proc is None:
            return
        try:
            if proc.stdin:
                proc.stdin.close()
        except Exception:
            pass
        try:
            if proc.stdout:
                proc.stdout.close()
        except Exception:
            pass

    def _ensure_engine_alive(self, replay_state=True):
        if self.engine is not None and self.engine.poll() is None:
            return
        self._close_engine_pipes(self.engine)
        self.engine = self._spawn_engine_process()
        self.ai.engine = self.engine
        if not replay_state:
            return
        if self.initial_fen and self.initial_fen != STANDARD_START_FEN:
            set_fen(self.engine, self.initial_fen)
        for past_move in list(self.move_history):
            resp = send_move_to_engine(self.engine, past_move)
            if resp != "MOVE_OK":
                raise RuntimeError(f"Failed restoring engine state on {past_move}: {resp}")

    def initial_position(self):
        threading.Thread(
            target=self.load_initial_position,
            daemon=True
        ).start()

    def _compute_live_ai_eval(self, status, turn):
        """Query the C++ AI+ search engine for real-time White-perspective centipawn evaluation."""
        if status == "CHECKMATE":
            return -100000 if turn == "WHITE" else 100000
        if status in GAME_OVER_STATUSES:
            return 0
        try:
            _, score_cp, _ = analyze_position_with_engine(
                self.engine,
                depth=4,
                time_limit_ms=160,
            )
            return int(score_cp)
        except Exception:
            if self.board:
                return int(round(evaluate_board(self.board)))
            return 0

    def load_initial_position(self):
        try:
            with self.engine_lock:
                self._ensure_engine_alive(replay_state=False)
                board, moves, status, turn = get_position(self.engine)
                engine_eval = get_engine_evaluation(self.engine)
                ai_eval = self._compute_live_ai_eval(status, turn)

            if not self.closing:
                self.root.after(
                    0,
                    lambda: self._finish_initial_load(
                        board, moves, status, turn, engine_eval, ai_eval
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

    def _finish_initial_load(self, board, moves, status, turn, engine_eval, ai_eval=None):
        self.update_position(
            board, moves, status, turn, engine_eval=engine_eval, ai_eval=ai_eval
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
        self._save_preferences()
        self.draw_board()

    def _save_preferences(self):
        if not self.settings_path or self.closing:
            return
        save_user_settings(
            {
                "board_theme": self.board_theme_name,
                "sound_enabled": bool(self.sound_enabled),
                "difficulty": self.difficulty_var.get(),
                "time_control": self.time_control_name,
                "game_mode": self.game_mode,
                "human_color": self.human_color,
            },
            path=self.settings_path,
        )

    def on_sidebar_difficulty_change(self, _choice=None):
        self._save_preferences()

    def apply_custom_time_control(self, minutes, increment, confirm_reset=False):
        label, spec = parse_custom_time_control(minutes, increment)
        if label not in TIME_CONTROLS:
            TIME_CONTROLS[label] = spec
            if hasattr(self, "time_menu"):
                menu = self.time_menu["menu"]
                idx_custom = menu.index("end")
                menu.insert_radiobutton(
                    max(0, idx_custom),
                    label=label,
                    variable=self.time_var,
                    value=label,
                    command=lambda ch=label: self.on_sidebar_time_change(ch)
                )
        self.time_var.set(label)
        if not self.move_history and self.game_status not in GAME_OVER_STATUSES:
            self._reset_clocks(label)
            self._start_clock()
            self._save_preferences()
            return label
        if (not confirm_reset) or messagebox.askyesno(
            "Change Time Control",
            f"Start a new game with {label}?"
        ):
            self.new_game(time_control=label)
        else:
            self.time_var.set(self.time_control_name)
        return label

    def prompt_custom_time_control(self):
        self._in_modal = True
        self._stop_clock()
        custom_vals = {"value": None}
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title("Custom Time Control")
            dialog.resizable(False, False)
            dialog.configure(bg=THEME["sidebar"])
            dialog.transient(self.root)
            dialog.grab_set()

            tk.Label(
                dialog,
                text="Custom Clock (Minutes + Increment)",
                font=("Segoe UI", 11, "bold"),
                fg=THEME["text"],
                bg=THEME["sidebar"],
                padx=20
            ).pack(pady=(14, 8))

            row = tk.Frame(dialog, bg=THEME["card"], padx=14, pady=10)
            row.pack(fill="x", padx=20, pady=(0, 10))

            tk.Label(row, text="Minutes (1–180):", font=("Segoe UI", 9, "bold"), fg=THEME["text"], bg=THEME["card"]).grid(row=0, column=0, sticky="w", pady=4)
            mins_entry = tk.Entry(row, width=8, font=("Consolas", 10), bg=THEME["list_bg"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", bd=4)
            mins_entry.insert(0, "5")
            mins_entry.grid(row=0, column=1, padx=(10, 0), pady=4)

            tk.Label(row, text="Increment sec (0–60):", font=("Segoe UI", 9, "bold"), fg=THEME["text"], bg=THEME["card"]).grid(row=1, column=0, sticky="w", pady=4)
            inc_entry = tk.Entry(row, width=8, font=("Consolas", 10), bg=THEME["list_bg"], fg=THEME["text"], insertbackground=THEME["text"], relief="flat", bd=4)
            inc_entry.insert(0, "3")
            inc_entry.grid(row=1, column=1, padx=(10, 0), pady=4)

            btn_row = tk.Frame(dialog, bg=THEME["sidebar"], padx=20)
            btn_row.pack(fill="x", pady=(0, 14))

            def on_apply():
                try:
                    mins = int(mins_entry.get().strip())
                    inc = int(inc_entry.get().strip())
                    parse_custom_time_control(mins, inc)
                    custom_vals["value"] = (mins, inc)
                    dialog.destroy()
                except Exception as exc:
                    messagebox.showerror("Invalid Time Control", str(exc), parent=dialog)

            tk.Button(
                btn_row,
                text="Apply",
                font=("Segoe UI", 10, "bold"),
                bg=THEME["accent_blue"],
                fg="#FFFFFF",
                relief="flat",
                bd=0,
                pady=6,
                cursor="hand2",
                command=on_apply
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
                cursor="hand2",
                command=dialog.destroy
            ).pack(side="left", expand=True, fill="x", padx=(4, 0))

            dialog.bind("<Return>", lambda _e: on_apply())
            dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
            dialog.update_idletasks()
            x = self.root.winfo_rootx() + (self.root.winfo_width() - dialog.winfo_width()) // 2
            y = self.root.winfo_rooty() + (self.root.winfo_height() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{max(0, x)}+{max(0, y)}")
            dialog.lift()
            self.root.wait_window(dialog)
        finally:
            self._in_modal = False

        if custom_vals["value"] is not None:
            mins, inc = custom_vals["value"]
            return self.apply_custom_time_control(mins, inc, confirm_reset=True)
        self.time_var.set(self.time_control_name)
        self._start_clock()
        return None

    def on_sidebar_time_change(self, choice):
        if self.engine_busy:
            self.time_var.set(self.time_control_name)
            return
        if choice == "Custom...":
            self.prompt_custom_time_control()
            return
        if choice not in TIME_CONTROLS:
            spec = resolve_time_control_spec(choice)
            if spec is not None:
                TIME_CONTROLS[choice] = spec
            else:
                self.time_var.set(self.time_control_name)
                return
        if choice == self.time_control_name:
            return
        if not self.move_history and self.game_status not in GAME_OVER_STATUSES:
            self._reset_clocks(choice)
            self._start_clock()
            self._save_preferences()
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
            fg=THEME["accent_soft"] if top_active else THEME["muted"]
        )
        self.top_clock_time.config(
            text=format_clock_time(top_val),
            fg="#F87171" if (top_val is not None and top_val < 15.0) else (
                "#FFFFFF" if top_active else THEME["text"]
            )
        )
        self.bottom_clock_name.config(
            text=bottom_name,
            fg=THEME["accent_soft"] if bottom_active else THEME["muted"]
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
        self._save_preferences()

    def set_board_theme(self, theme_name):
        if theme_name not in BOARD_THEMES:
            return
        self.board_theme_name = theme_name
        if hasattr(self, "theme_var"):
            self.theme_var.set(theme_name)
        self._save_preferences()
        self.draw_board()

    def _shortcut_allowed(self):
        if self.closing or self._in_modal:
            return False
        try:
            focus = self.root.focus_get()
            if isinstance(focus, (tk.Entry, tk.Text)):
                return False
        except Exception:
            pass
        return True

    def _bind_shortcuts(self):
        self.root.bind("<Left>", lambda _e: self._shortcut_allowed() and self.step_back())
        self.root.bind("<Right>", lambda _e: self._shortcut_allowed() and self.step_forward())
        self.root.bind("<Home>", lambda _e: self._shortcut_allowed() and (self._cancel_animation(), self._apply_view_index(0)))
        self.root.bind("<End>", lambda _e: self._shortcut_allowed() and self.jump_to_live())
        self.root.bind("<KeyPress-f>", lambda _e: self._shortcut_allowed() and self.flip_board())
        self.root.bind("<KeyPress-F>", lambda _e: self._shortcut_allowed() and self.flip_board())
        self.root.bind("<KeyPress-h>", lambda _e: self._shortcut_allowed() and self.request_hint())
        self.root.bind("<KeyPress-H>", lambda _e: self._shortcut_allowed() and self.request_hint())
        self.root.bind("<KeyPress-m>", lambda _e: self._shortcut_allowed() and self.toggle_sound())
        self.root.bind("<KeyPress-M>", lambda _e: self._shortcut_allowed() and self.toggle_sound())
        self.root.bind("<Escape>", lambda _e: self._shortcut_allowed() and self._clear_board_annotations())

    def _clear_board_annotations(self):
        self.selected_square = None
        self.selected_moves = []
        self.premove = None
        self._premove_selected = None
        self.user_arrows.clear()
        self.highlighted_squares.clear()
        self.hint_move = None
        self.draw_board()

    def on_history_click(self, event):
        if self.engine_busy or not self.position_history or self.history_list.size() == 0:
            return
        row = self.history_list.nearest(event.y)
        bbox = self.history_list.bbox(row)
        if not bbox:
            return
        bx, by, bw, bh = bbox
        if event.y < by or event.y > by + bh:
            return

        white_idx = row * 2 + 1
        black_idx = row * 2 + 2
        if white_idx >= len(self.position_history):
            return

        width = max(1, self.history_list.winfo_width())
        if black_idx < len(self.position_history) and event.x >= width * 0.52:
            target_idx = black_idx
        else:
            target_idx = white_idx

        self._cancel_animation()
        self._apply_view_index(target_idx)

    def _draw_eval_graph(self):
        if not hasattr(self, "eval_graph"):
            return
        gw = self.eval_graph.winfo_width()
        gh = self.eval_graph.winfo_height()
        if gw <= 4 or gh <= 4:
            return

        self.eval_graph.delete("all")
        mid_y = gh / 2.0
        self.eval_graph.create_rectangle(0, 0, gw, mid_y, fill=THEME["graph_top"], outline="")
        self.eval_graph.create_rectangle(0, mid_y, gw, gh, fill=THEME["graph_bottom"], outline="")
        self.eval_graph.create_line(0, mid_y, gw, mid_y, fill=THEME["border"], width=1)

        n = len(self.eval_history)
        if n == 0:
            return

        col_w = gw / max(1, n)
        for idx, score_pawns in enumerate(self.eval_history):
            clamped = max(-8.0, min(8.0, float(score_pawns)))
            x1 = idx * col_w
            x2 = max(x1 + 1.5, (idx + 1) * col_w)
            bar_h = (abs(clamped) / 8.0) * (mid_y - 2)
            if clamped >= 0:
                self.eval_graph.create_rectangle(
                    x1, mid_y - bar_h, x2, mid_y,
                    fill="#E2E8F0", outline=""
                )
            else:
                self.eval_graph.create_rectangle(
                    x1, mid_y, x2, mid_y + bar_h,
                    fill="#64748B", outline=""
                )

        if 0 <= self.view_index < n:
            mx = (self.view_index + 0.5) * col_w
            self.eval_graph.create_line(mx, 0, mx, gh, fill=THEME["accent_badge_fg"], width=2)

    def on_eval_graph_click(self, event):
        if self.engine_busy or not self.position_history or not self.eval_history:
            return
        gw = max(1, self.eval_graph.winfo_width())
        idx = int((event.x / gw) * len(self.eval_history))
        idx = max(0, min(len(self.position_history) - 1, idx))
        self._cancel_animation()
        self._apply_view_index(idx)

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
                self._ensure_engine_alive(replay_state=False)
                ok = set_fen(self.engine, fen_str)
                if not ok:
                    raise ValueError(f"Invalid FEN string:\n{fen_str}")
                board, moves, status, turn = get_position(self.engine)
                engine_eval = get_engine_evaluation(self.engine)
                ai_eval = self._compute_live_ai_eval(status, turn)
                loaded_fen = get_fen(self.engine)

            if not self.closing:
                self.root.after(
                    0,
                    lambda: self._apply_loaded_fen(
                        board, moves, status, turn, engine_eval, loaded_fen, ai_eval
                    )
                )
        except Exception as e:
            if not self.closing:
                self.root.after(
                    0,
                    lambda err=str(e): self._handle_move_error("FEN Error", err)
                )

    def _apply_loaded_fen(self, board, moves, status, turn, engine_eval, loaded_fen, ai_eval=None):
        if self.closing:
            return
        self._cancel_animation()
        self.initial_fen = loaded_fen
        self.selected_square = None
        self.selected_moves = []
        self.premove = None
        self._premove_selected = None
        self.user_arrows.clear()
        self.highlighted_squares.clear()
        self.last_move = None
        self.hint_move = None
        self.move_history = []
        self.san_history = []
        self.captured_by_white = []
        self.captured_by_black = []
        self.position_history = []
        self.eval_history = []
        self.review_annotations = []
        self.review_summary = None
        self.review_best_move = None
        self.view_index = -1
        self._reset_clocks(self.time_control_name)
        self.update_move_history()
        self.update_position(board, moves, status, turn, engine_eval=engine_eval, ai_eval=ai_eval)
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
                activebackground=THEME["accent_primary_hover"],
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
        can_review = (
            not self.engine_busy
            and not self.review_busy
            and len(self.move_history) > 0
        )
        self.review_game_button.config(
            text="🔍 Reviewing..." if self.review_busy else "🔍 Review",
            state="normal" if can_review else "disabled"
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
            fill="#F8FAFC",
            outline=""
        )
        self.eval_bar.create_rectangle(
            split_x, 0, bar_width, bar_height,
            fill=THEME["list_bg"],
            outline=""
        )
        mid_x = bar_width // 2
        self.eval_bar.create_line(
            mid_x, 0, mid_x, bar_height,
            fill="#64748B",
            width=1
        )

    def _format_live_ai_display(self, ai_cp):
        """Format White-perspective AI+ centipawn/mate score for the headline and eval bar."""
        if abs(ai_cp) >= 100000:
            if ai_cp > 0:
                return "White wins (Mate)", "WHITE", 20.0, "+M0"
            return "Black wins (Mate)", "BLACK", -20.0, "-M0"
        if abs(ai_cp) >= 90000:
            mate_in = max(1, (100000 - abs(ai_cp) + 1) // 2)
            if ai_cp > 0:
                return f"White has Mate in M{mate_in}", "WHITE", 20.0, f"+M{mate_in}"
            return f"Black has Mate in M{mate_in}", "BLACK", -20.0, f"-M{mate_in}"
        ai_pawns = ai_cp / 100.0
        headline, side, _ = format_evaluation_summary(ai_pawns)
        ai_sign = "+" if ai_pawns > 0 else ""
        return headline, side, ai_pawns, f"{ai_sign}{ai_pawns:.2f}"

    def update_evaluation_panel(self, board, engine_eval=None, ai_eval=None):
        if self.closing or not board:
            return

        if engine_eval is not None:
            self.engine_eval = engine_eval
        if ai_eval is not None:
            self.ai_eval_cp = int(ai_eval)
        elif engine_eval is None and not self.position_history:
            self.ai_eval_cp = int(round(evaluate_board(board)))

        material = analyze_material(board)
        material_score = material["score"]
        self.current_material_score = material_score

        headline, side, bar_score, ai_display = self._format_live_ai_display(self.ai_eval_cp)
        self.current_eval_score = bar_score

        dark_colors = {
            "WHITE": "#4ADE80",
            "BLACK": "#F87171",
            "EQUAL": "#E5E7EB",
        }
        self.eval_headline_label.config(
            text=headline,
            fg=dark_colors.get(side, "#E5E7EB")
        )
        self._draw_eval_bar(bar_score)

        self.ai_eval_label.config(
            text=f"AI Positional Eval (Search AI+): {ai_display}"
        )

        cpp_score = self.engine_eval if engine_eval is None else engine_eval
        cpp_sign = "+" if cpp_score > 0 else ""
        self.engine_eval_label.config(
            text=f"C++ Engine Eval (material-only): {cpp_sign}{cpp_score:.1f}"
        )

        wc = material["white_counts"]
        bc = material["black_counts"]
        self.white_material_label.config(
            text=(
                f"W: Q{wc['Q']} R{wc['R']} "
                f"B{wc['B']} N{wc['N']} P{wc['P']}"
            )
        )
        self.black_material_label.config(
            text=(
                f"B: q{bc['Q']} r{bc['R']} "
                f"b{bc['B']} n{bc['N']} p{bc['P']}"
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
        ai_eval=None,
        animate_from=None,
        animate_steps=8,
        animate_frame_ms=16
    ):
        if self.closing:
            return

        self._cancel_animation()
        self.hint_move = None
        self.user_arrows.clear()
        self.highlighted_squares.clear()
        self.board = [row[:] for row in board]
        self.legal_moves = moves
        self.game_status = status
        self.white_turn = turn == "WHITE"
        if last_move is not None:
            self.last_move = last_move
        if appended_move is not None:
            self.move_history.append(appended_move)
            self.san_history.append(appended_san or appended_move)
            self.review_annotations = []
            self.review_summary = None
            self.review_best_move = None
            if captured_piece is not None:
                if captured_piece.islower():
                    self.captured_by_white.append(captured_piece)
                else:
                    self.captured_by_black.append(captured_piece)

        resolved_ai_cp = (
            int(ai_eval)
            if ai_eval is not None
            else int(round(evaluate_board(board)))
        )
        self.ai_eval_cp = resolved_ai_cp
        ai_pawns_eval = max(-8.0, min(8.0, resolved_ai_cp / 100.0))
        snapshot = {
            "board": [row[:] for row in board],
            "status": status,
            "white_turn": (turn == "WHITE"),
            "last_move": self.last_move,
            "engine_eval": self.engine_eval if engine_eval is None else engine_eval,
            "ai_eval": resolved_ai_cp,
            "captured_by_white": list(self.captured_by_white),
            "captured_by_black": list(self.captured_by_black),
        }
        if appended_move is not None or not self.position_history:
            self.position_history.append(snapshot)
            self.eval_history.append(ai_pawns_eval)
        else:
            self.position_history[-1] = snapshot
            if self.eval_history:
                self.eval_history[-1] = ai_pawns_eval
            else:
                self.eval_history.append(ai_pawns_eval)
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
            self.premove = None
            self._premove_selected = None
            self._stop_clock()

        self.update_evaluation_panel(board, engine_eval=engine_eval, ai_eval=resolved_ai_cp)
        self._update_opening_banner(self.view_index)
        self._draw_eval_graph()
        self._refresh_clocks()
        self._update_controls()

        queued_premove = None
        if (
            not keep_busy
            and self.premove
            and self.game_status not in GAME_OVER_STATUSES
            and can_human_interact(self.game_mode, self.white_turn, self.human_color)
        ):
            for lm in self.legal_moves:
                if lm == self.premove or (lm[:4] == self.premove[:4] and (len(lm) == 4 or lm.endswith("q"))):
                    queued_premove = lm
                    break
            self.premove = None
            self._premove_selected = None

        if queued_premove is not None:
            self.draw_board()
            self.root.after(20, lambda pm=queued_premove: self.make_move(pm, animate=False))
            return

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
                    total_steps=animate_steps,
                    frame_ms=animate_frame_ms,
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

    def _can_premove_now(self):
        return (
            self.game_mode == MODE_PVAI
            and self.engine_busy
            and self.is_viewing_live()
            and self.game_status not in GAME_OVER_STATUSES
            and bool(self.board)
        )

    def _handle_premove_click(self, clicked_square, row, col):
        human_is_white = (self.human_color == HUMAN_COLOR_WHITE)
        piece = self.board[row][col]
        if self._premove_selected is None:
            if is_own_piece(piece, human_is_white):
                self._premove_selected = clicked_square
                self.premove = None
                self.draw_board()
            elif self.premove is not None:
                self.premove = None
                self.draw_board()
            return

        if clicked_square == self._premove_selected:
            self._premove_selected = None
            self.draw_board()
            return

        if is_own_piece(piece, human_is_white):
            self._premove_selected = clicked_square
            self.draw_board()
            return

        from_sq = self._premove_selected
        self._premove_selected = None
        fr, fc = notation_to_coords(from_sq)
        moving_piece = self.board[fr][fc]
        suffix = ""
        if moving_piece.lower() == "p" and row in (0, 7):
            suffix = "q"
        self.premove = from_sq + clicked_square + suffix
        self.draw_board()

    def on_right_down(self, event):
        coords = self._event_to_board_square(event)
        if coords is None:
            self._right_drag_start = None
            return
        self._right_drag_start = coords[2]

    def on_right_up(self, event):
        start_sq = self._right_drag_start
        self._right_drag_start = None
        if self.premove is not None or self._premove_selected is not None:
            self.premove = None
            self._premove_selected = None
            self.draw_board()
            return
        if not start_sq:
            return
        coords = self._event_to_board_square(event)
        if coords is None:
            return
        end_sq = coords[2]
        if end_sq == start_sq:
            if start_sq in self.highlighted_squares:
                self.highlighted_squares.remove(start_sq)
            else:
                self.highlighted_squares.add(start_sq)
        else:
            arrow = (start_sq, end_sq)
            if arrow in self.user_arrows:
                self.user_arrows.remove(arrow)
            else:
                self.user_arrows.append(arrow)
        self.draw_board()

    def on_mouse_down(self, event):
        self._drag_state = None
        self.user_arrows.clear()
        self.highlighted_squares.clear()

        coords = self._event_to_board_square(event)
        if coords is None:
            self.draw_board()
            return
        row, col, clicked_square = coords

        if self._can_premove_now():
            self._handle_premove_click(clicked_square, row, col)
            return

        if not self._can_interact_now():
            self.draw_board()
            return
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
                self._ensure_engine_alive(replay_state=True)
                try:
                    response = send_move_to_engine(
                        self.engine, move
                    )
                except OSError:
                    # Recover once if underlying engine pipe closed unexpectedly
                    self._close_engine_pipes(self.engine)
                    self.engine = None
                    self._ensure_engine_alive(replay_state=True)
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
                ai_eval = self._compute_live_ai_eval(status, turn)

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
                        ai_eval=ai_eval,
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
            t_start = time.monotonic()

            with self.engine_lock:
                self._ensure_engine_alive(replay_state=True)
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
                ai_eval = self._compute_live_ai_eval(status, turn)

            elapsed = time.monotonic() - t_start
            if elapsed < 0.22 and not self.closing:
                time.sleep(0.22 - elapsed)

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
                        ai_eval=ai_eval,
                        animate_from=anim_pair,
                        animate_steps=20,
                        animate_frame_ms=25
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
                self._ensure_engine_alive(replay_state=True)
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

    def _update_opening_banner(self, upto_ply=None):
        if not hasattr(self, "opening_label"):
            return
        ply = self.view_index if upto_ply is None else upto_ply
        if ply < 0:
            ply = len(self.move_history)
        self.opening_name = detect_opening_name(
            self.move_history[:max(0, ply)],
            self.initial_fen
        )
        if self.review_summary is not None:
            self.opening_label.config(
                text=(
                    f"{self.opening_name} · "
                    f"W {self.review_summary['white_acc']:.1f}% | "
                    f"B {self.review_summary['black_acc']:.1f}%"
                )
            )
        else:
            self.opening_label.config(text=f"Opening: {self.opening_name}")

    def review_game(self):
        if self.engine_busy or self.review_busy or not self.move_history:
            return
        self.review_busy = True
        self._update_controls()
        moves_copy = list(self.move_history)
        start_fen = self.initial_fen
        threading.Thread(
            target=self._run_game_review,
            args=(moves_copy, start_fen),
            daemon=True
        ).start()

    def _run_game_review(self, moves_list, start_fen):
        proc = None
        annotations = []
        eval_history_pawns = []
        white_losses = []
        black_losses = []
        try:
            proc = self._spawn_engine_process()
            if start_fen and start_fen != STANDARD_START_FEN:
                set_fen(proc, start_fen)

            positions_cache = []
            # Collect pre-move position info + score sequentially
            board, legal, status, turn = get_position(proc)
            _, cur_eval_cp, _ = analyze_position_with_engine(proc, depth=3, time_limit_ms=130)
            positions_cache.append((board, legal, status, turn, cur_eval_cp))
            eval_history_pawns.append(max(-8.0, min(8.0, cur_eval_cp / 100.0)))

            best_moves = []
            for idx, mv in enumerate(moves_list):
                board_b, legal_b, _, turn_b, pre_eval_cp = positions_cache[idx]
                best_mv, _, _ = analyze_position_with_engine(proc, depth=3, time_limit_ms=130)
                best_moves.append((board_b, legal_b, turn_b, pre_eval_cp, best_mv))

                resp = send_move_to_engine(proc, mv)
                if resp != "MOVE_OK":
                    raise RuntimeError(f"Review move rejected: {mv} -> {resp}")
                next_board, next_legal, next_status, next_turn = get_position(proc)
                if next_status == "CHECKMATE":
                    after_eval_cp = -10000 if next_turn == "WHITE" else 10000
                elif next_status in GAME_OVER_STATUSES:
                    after_eval_cp = 0
                else:
                    _, after_eval_cp, _ = analyze_position_with_engine(
                        proc, depth=3, time_limit_ms=130
                    )
                positions_cache.append((next_board, next_legal, next_status, next_turn, after_eval_cp))
                eval_history_pawns.append(max(-8.0, min(8.0, after_eval_cp / 100.0)))

            for idx, mv in enumerate(moves_list):
                board_b, legal_b, turn_b, pre_eval_cp, best_mv = best_moves[idx]
                after_eval_cp = positions_cache[idx + 1][4]

                pre_clamped = max(-1500, min(1500, pre_eval_cp))
                after_clamped = max(-1500, min(1500, after_eval_cp))
                is_white = (turn_b == "WHITE")
                cp_loss = (
                    max(0, pre_clamped - after_clamped)
                    if is_white
                    else max(0, after_clamped - pre_clamped)
                )
                is_best = (best_mv is not None and mv == best_mv)
                symbol, label = classify_cp_loss(cp_loss, is_best_move=is_best)

                best_san = (
                    format_san_move(board_b, legal_b, best_mv)
                    if best_mv else ""
                )
                if is_white:
                    white_losses.append(cp_loss)
                else:
                    black_losses.append(cp_loss)

                annotations.append({
                    "symbol": symbol,
                    "label": label,
                    "cp_loss": cp_loss,
                    "best_uci": best_mv,
                    "best_san": best_san,
                    "eval_pawns": after_eval_cp / 100.0,
                })

            summary = {
                "white_acc": calculate_accuracy(white_losses),
                "black_acc": calculate_accuracy(black_losses),
                "inaccuracies": sum(1 for a in annotations if a["symbol"] == "?!"),
                "mistakes": sum(1 for a in annotations if a["symbol"] == "?"),
                "blunders": sum(1 for a in annotations if a["symbol"] == "??"),
            }
            if not self.closing:
                self.root.after(
                    0,
                    lambda: self._finish_game_review(
                        annotations, summary, eval_history_pawns
                    )
                )
        except Exception as e:
            if not self.closing:
                self.root.after(
                    0,
                    lambda err=str(e): self._fail_game_review(err)
                )
        finally:
            if proc is not None:
                try:
                    if proc.poll() is None:
                        proc.terminate()
                        proc.wait(timeout=2)
                    if proc.stdin:
                        proc.stdin.close()
                    if proc.stdout:
                        proc.stdout.close()
                except Exception:
                    pass

    def _finish_game_review(self, annotations, summary, eval_history_pawns):
        if self.closing:
            return
        self.review_busy = False
        if len(annotations) == len(self.move_history):
            self.review_annotations = annotations
            self.review_summary = summary
            if len(eval_history_pawns) == len(self.position_history):
                self.eval_history = eval_history_pawns
            self._apply_view_index(self.view_index)
            self.update_move_history()
            self._highlight_history_for_view(self.view_index)
            self._update_opening_banner(self.view_index)
            self._draw_eval_graph()
        self._update_controls()
        self.draw_board()

    def _fail_game_review(self, err):
        if self.closing:
            return
        self.review_busy = False
        self._update_controls()
        messagebox.showerror("Review Error", err)

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
        self.review_best_move = None
        if (
            self.review_annotations
            and idx > 0
            and idx - 1 < len(self.review_annotations)
        ):
            ann = self.review_annotations[idx - 1]
            if ann["symbol"] in ("?!", "?", "??") and ann["best_uci"]:
                self.review_best_move = ann["best_uci"]

        self.update_evaluation_panel(
            self.board,
            engine_eval=snapshot["engine_eval"],
            ai_eval=snapshot.get("ai_eval")
        )
        if (
            self.review_annotations
            and idx > 0
            and idx - 1 < len(self.review_annotations)
        ):
            ann = self.review_annotations[idx - 1]
            played_san = (
                self.san_history[idx - 1]
                if idx - 1 < len(self.san_history)
                else self.move_history[idx - 1]
            )
            detail = f"{played_san}{ann['symbol']} ({ann['label']})"
            if ann["symbol"] in ("?!", "?", "??") and ann["best_san"]:
                detail += f" — Best: {ann['best_san']}"
            self.material_diff_label.config(text=detail)
        self._update_opening_banner(idx)
        self._draw_eval_graph()
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
                self._ensure_engine_alive(replay_state=False)
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
                ai_eval = self._compute_live_ai_eval(status, turn)

            if not self.closing:
                self.root.after(
                    0,
                    lambda: self._apply_new_game_state(
                        board, moves, status, turn, engine_eval, selected_config, ai_eval
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
        selected_config=None,
        ai_eval=None
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
        self.premove = None
        self._premove_selected = None
        self.user_arrows.clear()
        self.highlighted_squares.clear()
        self.last_move = None
        self.hint_move = None
        self.move_history = []
        self.san_history = []
        self.captured_by_white = []
        self.captured_by_black = []
        self.initial_fen = STANDARD_START_FEN
        self.position_history = []
        self.eval_history = []
        self.review_annotations = []
        self.review_summary = None
        self.review_best_move = None
        self.view_index = -1
        self.update_move_history()
        self.update_position(board, moves, status, turn, engine_eval=engine_eval, ai_eval=ai_eval)
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
        annotated = []
        for idx, mv in enumerate(display_moves):
            sym = ""
            if idx < len(self.review_annotations):
                sym = self.review_annotations[idx].get("symbol", "")
            annotated.append(f"{mv}{sym}")

        for i in range(0, len(annotated), 2):

            move_number = (i // 2) + 1
            white_move = annotated[i]

            if i + 1 < len(annotated):

                black_move = annotated[i + 1]

                text = (
                    f"{move_number:>2}. "
                    f"{white_move:<8} "
                    f"{black_move}"
                )

            else:

                text = (
                    f"{move_number:>2}. "
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

        palette = BOARD_THEMES.get(self.board_theme_name, BOARD_THEMES["Classic Green"])
        light = palette["light"]
        dark = palette["dark"]
        selected_color = palette["selected"]
        last_move_light = palette["last_light"]
        last_move_dark = palette["last_dark"]
        check_color = palette["check"]

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

                if square in self.highlighted_squares:
                    color = "#34D399" if is_light else "#059669"

                if self.premove and (square == self.premove[:2] or square == self.premove[2:4]):
                    color = "#FCA5A5" if is_light else "#EF4444"

                if square == self._premove_selected:
                    color = "#FBBF24"

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
                            outline=palette["ring"],
                            width=max(3, int(square_size * 0.08))
                        )
                    else:
                        dot_r = square_size * 0.16
                        self.canvas.create_oval(
                            cx - dot_r,
                            cy - dot_r,
                            cx + dot_r,
                            cy + dot_r,
                            fill=palette["dot_dark"] if not is_light else palette["dot_light"],
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

        for from_sq, to_sq in self.user_arrows:
            self._draw_board_arrow(from_sq, to_sq, offset_x, offset_y, square_size, "#10B981")

        if (
            self.review_best_move
            and len(self.review_best_move) >= 4
            and not self.hint_move
        ):
            self._draw_board_arrow(
                self.review_best_move[:2],
                self.review_best_move[2:4],
                offset_x,
                offset_y,
                square_size,
                "#38BDF8"
            )

        if (
            self.hint_move
            and len(self.hint_move) >= 4
            and viewing_live
        ):
            self._draw_board_arrow(
                self.hint_move[:2],
                self.hint_move[2:4],
                offset_x,
                offset_y,
                square_size,
                "#F59E0B"
            )

    def _draw_board_arrow(self, from_sq, to_sq, offset_x, offset_y, square_size, color):
        from_r, from_c = notation_to_coords(from_sq)
        to_r, to_c = notation_to_coords(to_sq)
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
            fill=color,
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
