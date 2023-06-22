player_colors = {
    "w": (240, 230, 206),
    "b": (138, 110, 69)  # "#61573e",
}

board_color = {
    "w": 0,
    "b": 1
}

col_int_to_str = {v: k for k, v in board_color.items()}


def get_opponent_color(player_col):
    return player_col ^ 1  # XOR


def grid2continous(row, col, board_dim=8):
    return (row*board_dim) + col


def continous2grid(idx, board_dim=8):
    row = idx//board_dim
    col = idx % board_dim
    return row, col


highlight_color = (245, 85, 73)
last_move_color = (242, 196, 90)
attack_color = (242, 210, 170)

piece_types = {
    1: "Pawn",
    2: "Knight",
    3: "Bishop",
    4: "Rook",
    5: "Queen",
    6: "King"
}

piece_str_to_type = {v: k for k, v in piece_types.items()}

piece_values = {
    1: 1,
    2: 3,
    3: 3,
    4: 5,
    5: 9,
    6: 15
}

fen_codec = {
    "p": piece_str_to_type["Pawn"],
    "n": piece_str_to_type["Knight"],
    "b": piece_str_to_type["Bishop"],
    "r": piece_str_to_type["Rook"],
    "q": piece_str_to_type["Queen"],
    "k": piece_str_to_type["King"],
}

fen_codec_reverse = {v: k for k, v in fen_codec.items()}

fen_string = {
    "start": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
}


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


move_desc = {
    0:  "quiet",
    1: 	"pawn_double",
    2: 	"castle_king",
    3: 	"castle_queen",
    4: 	"capture",
    5: 	"ep_capture",
    8: 	"promo_n",
    9: 	"promo_b",
    10: "promo_r",
    11: "promo_q",
    12: "promo_capture_n",
    13: "promo_capture_b",
    14: "promo_capture_r",
    15: "promo_capture_q",
}
move_types = {v: k for k, v in move_desc.items()}

move_promo_to_piece = {
    8: 	piece_str_to_type["Knight"],
    9: 	piece_str_to_type["Bishop"],
    10: piece_str_to_type["Rook"],
    11: piece_str_to_type["Queen"],
    12: piece_str_to_type["Knight"],
    13: piece_str_to_type["Bishop"],
    14: piece_str_to_type["Rook"],
    15: piece_str_to_type["Queen"],
}


def print_board_string(orig, dest, pieces, colors, board_dim=8):
    for row in range(board_dim):
        print("  " + "-"*33)
        row_str = str(board_dim-row) + " "
        for col in range(board_dim):
            row_str += "|"
            i = grid2continous(row, col)
            if i == orig or i == dest:
                row_str += bcolors.WARNING
            if pieces[i] < 0:
                row_str += " - "
            else:
                fen_letter = str(fen_codec_reverse[pieces[i]])
                if colors[i] == 0:
                    fen_letter = fen_letter.upper()
                row_str += " " + fen_letter + " "
            if i == orig or i == dest:
                row_str += bcolors.ENDC
        row_str += "|" + "   <- " + str(i)
        print(row_str)
    print("  " + "-"*33)
    print("    a   b   c   d   e   f   g   h")
