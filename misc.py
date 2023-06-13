player_colors = {
    "w": (240, 230, 206),
    "b": (138, 110, 69)#"#61573e",
}

board_color = {
    "w": 0,
    "b": 1
}

col_int_to_str = {v: k for k,v in board_color.items()}

def get_opponent_color(player_col):
    return player_col ^ 1 #XOR

def grid2continous(row, col, board_dim=8):
    return (row*board_dim) + col
def continous2grid(idx, board_dim=8):
    row = idx//board_dim
    col = idx%board_dim
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

piece_str_to_type = {v: k for k,v in piece_types.items()}

piece_values = {
    1: 1,
    2: 3,
    3: 3,
    4: 5,
    5: 9,
    6: 15   
}