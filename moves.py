import numpy as np
from misc import *
from collections import defaultdict

class MoveGen:
    def __init__(self):
        #    Now we have the mailbox array, so called because it looks like a
        #    mailbox, at least according to Bob Hyatt. This is useful when we
        #    need to figure out what pieces can go where. Let's say we have a
        #    rook on square a4 (32) and we want to know if it can move one
        #    square to the left. We subtract 1, and we get 31 (h5). The rook
        #    obviously can't move to h5, but we don't know that without doing
        #    a lot of annoying work. Sooooo, what we do is figure out a4's
        #    mailbox number, which is 61. Then we subtract 1 from 61 (60) and
        #    see what mailbox[60] is. In this case, it's -1, so it's out of
        #    bounds and we can forget it. You can see how mailbox[] is used
        #    in attack() in board.c. */ 
        self.mailbox = np.array([-1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
                                 -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
                                 -1,  0,  1,  2,  3,  4,  5,  6,  7, -1,
                                 -1,  8,  9, 10, 11, 12, 13, 14, 15, -1,
                                 -1, 16, 17, 18, 19, 20, 21, 22, 23, -1,
                                 -1, 24, 25, 26, 27, 28, 29, 30, 31, -1,
                                 -1, 32, 33, 34, 35, 36, 37, 38, 39, -1,
                                 -1, 40, 41, 42, 43, 44, 45, 46, 47, -1,
                                 -1, 48, 49, 50, 51, 52, 53, 54, 55, -1,
                                 -1, 56, 57, 58, 59, 60, 61, 62, 63, -1,
                                 -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
                                 -1, -1, -1, -1, -1, -1, -1, -1, -1, -1])
        self.mailbox64 = np.array([21, 22, 23, 24, 25, 26, 27, 28,
                                   31, 32, 33, 34, 35, 36, 37, 38,
                                   41, 42, 43, 44, 45, 46, 47, 48,
                                   51, 52, 53, 54, 55, 56, 57, 58,
                                   61, 62, 63, 64, 65, 66, 67, 68,
                                   71, 72, 73, 74, 75, 76, 77, 78,
                                   81, 82, 83, 84, 85, 86, 87, 88,
                                   91, 92, 93, 94, 95, 96, 97, 98])
        self.offsets = {
            1: [0, np.array([0,   0,  0,  0, 0,  0,  0,  0])], #Pawn
            2: [8, np.array([-21, -19,-12, -8, 8, 12, 19, 21])], #Knight
            3: [4, np.array([-11,  -9,  9, 11, 0,  0,  0,  0])], #Bishop
            4: [4, np.array([-10,  -1,  1, 10, 0,  0,  0,  0])], # Rook
            5: [8, np.array([-11, -10, -9, -1, 1,  9, 10, 11])],
            6: [8, np.array([-11, -10, -9, -1, 1,  9, 10, 11])],
        }
        self.slide = [False, False, False, True, True, True, False] #Empty, Pawn, Knight, Bishop, Rook, Queen, King

        self.first_rows = [[48,55], [8, 15]] #b, w pawn row indices
        self.pawn_moves = [[-8, -16], [8, 16]]
        self.pawn_captures = [[-7, -9], [7, 9]]
        self.pawn_captures64 = [[-9, -11], [9, 11]]
        self.en_passant_piece_idx = None
        self.pawn_capture_indices = set()
        self.king_moved = [False, False]
        self.rook_moved_l_s = [[False, False], [False, False]]
        self.king_rook_l_s = [[np.array([57,58, 59]), np.array([61, 62])], [np.array([1, 2, 3]), np.array([5, 6])]]
        self.rook_idx_l_s = [[56, 63], [0, 7]]
        

        self.protected = [set(), set()] # protected square for both sides [white protected indices, black]
        self.check_indices = defaultdict(list)
        self.pin_indices = defaultdict(list)
        self.allowed_moves_piece = defaultdict(list)
        self.pins = [set(), set()] #0: white pins which black pieces, 1: vice versa
        self.checks = set()

    def check_en_passant(self, pieces, colors, last_move):
        orig, dest = last_move
        if pieces[dest] == 1: # pawn moved last
            if abs(dest - orig) == abs(self.pawn_moves[0][1]): # 2 move forward
                player_col = colors[dest]
                opponent_col = get_opponent_color(player_col)
                #return set([orig, orig+self.pawn_moves[player_col][0]]), opponent_col
                return set([orig+self.pawn_moves[player_col][0]]), opponent_col
        return None, None
            
    def reset_board_states(self, reset_check=False):
        self.protected = [set(), set()]
        self.pin_indices = defaultdict(list)
        self.allowed_moves_piece = defaultdict(list)
        self.pins = [set(), set()]
        if reset_check:
            self.check_indices = defaultdict(list)
            self.checks = set()

    def allowed_moves(self, orig, piece, pieces, colors, last_move):
        capture_moves = set()
        other_moves = set()
        pin = []
        checks = []
        piece_color = colors[orig]

        if piece != 1: #no pawn
            for i in range(self.offsets[piece][0]):
                idx = orig
                expand_piece_cnt = 0
                expand_piece_idx = 0
                expanding = True
                all_idx = []
                last_expand_same_col = False
                while expanding:
                    all_idx.append(idx)
                    idx = self.mailbox[self.mailbox64[idx] + self.offsets[piece][1][i]]
                    if idx == -1:
                        break
                    if pieces[idx] >= 0: # capture moves
                        if piece_color != colors[idx]: # enemy field capture
                            last_expand_same_col = False
                            if piece == piece_str_to_type["King"]:
                                if idx in self.protected[get_opponent_color(piece_color)]:
                                    expanding = False
                                    break

                            if expand_piece_cnt > 0:
                                if pieces[idx] == piece_str_to_type["King"]:
                                    self.pin_indices[expand_piece_idx] = (all_idx)
                                    pin.append(expand_piece_idx)
                                #capture_moves.add(idx)
                                expanding = False
                            else:
                                if pieces[idx] == piece_str_to_type["King"]:
                                    self.check_indices[all_idx[0]] = all_idx
                                    checks.append(all_idx[0])
                                    expanding = False
                                else:
                                    expand_piece_idx = idx                   
                                capture_moves.add(idx)
                        else: # field of same color
                            last_expand_same_col = True
                            if expand_piece_cnt > 0:
                                expanding = False
                            else:
                                self.protected[piece_color].add(idx)
                        expand_piece_cnt += 1
                    else: # free space move
                        if piece == piece_str_to_type["King"]:
                            if idx in self.protected[get_opponent_color(piece_color)]:
                                    expanding = False
                                    break
                            other_moves.update(self.check_castling(orig, pieces, colors))
                        if expand_piece_cnt < 1 or not self.slide[piece]:
                            self.protected[piece_color].add(idx)
                            other_moves.add(idx)
                        if last_expand_same_col:
                            expanding = False
                        last_expand_same_col = False
                    if not self.slide[piece]:
                        expanding = False

        else:
            pawn_captures, pawn_moves = self.check_pawn_moves(orig, colors, pieces, last_move)
            other_moves.update(pawn_moves)
            capture_moves.update(pawn_captures)

        if orig in self.pins[get_opponent_color(piece_color)]: # check if piece is pinned by enemy
            capture_moves = set([self.pin_indices[orig][0]]).intersection(capture_moves) # capture pinning piece
            other_moves = set(self.pin_indices[orig][1:]).intersection(other_moves)

        if len(self.checks) > 0:
            # check exists
            if len(self.checks) == 1:
                if piece != piece_str_to_type["King"]: 
                    other_moves = other_moves.intersection(self.check_indices[next(iter(self.checks))]) #move piece other than king in way
                     #capture attacking piece
                elif piece == piece_str_to_type["King"]: #move king out to free square
                    other_moves = other_moves - set(self.check_indices[next(iter(self.checks))])
                capture_moves = set(self.checks).intersection(capture_moves)
            else: # > 1 check
                capture_moves = set()
                if piece == piece_str_to_type["King"]:
                    for nr_check in self.checks:
                        other_moves = other_moves - self.check_indices[nr_check] # find if free unchecked square exists

        self.allowed_moves_piece[orig] = capture_moves.union(other_moves)
        if len(pin) > 0:
            self.pins[piece_color].add(pin[0])
        if len(checks) > 0:
            self.checks.add(checks[0])
        #self.allowed_moves = self.capture_moves.union(self.other_moves)
        return capture_moves, other_moves
    
    

    def check_pawn_moves(self, orig, colors, pieces, last_move):
        orig_color = colors[orig]
        capture_moves = set()
        other_moves = set()
        move_1_fwrd = orig+self.pawn_moves[orig_color][0]
        move_2_fwrd = orig+self.pawn_moves[orig_color][1]
        move_l_cptr = orig+self.pawn_captures[orig_color][0]
        move_r_cptr = orig+self.pawn_captures[orig_color][1]

        
        if pieces[move_1_fwrd] < 0: # check free space
            other_moves.add(move_1_fwrd)
            if self.first_rows[orig_color][0] <= orig <= self.first_rows[orig_color][1]: # case 2 moves allowed from 1st row
                if pieces[move_2_fwrd] < 0:
                    other_moves.add(move_2_fwrd)
        
        # check captures with board boundaries
        en_passant_color = None
        self.pawn_capture_indices = set()
        for move_idx, move_type in zip([0, 1],[move_l_cptr, move_r_cptr]):
            if self.mailbox[self.mailbox64[orig]+self.pawn_captures64[orig_color][move_idx]] > -1:
                if colors[move_type]  == get_opponent_color(orig_color):
                    capture_moves.add(move_type)
                else:
                    if en_passant_color is None:
                        en_passant_indices, en_passant_color = self.check_en_passant(pieces, colors, last_move)
                    if en_passant_color == orig_color:
                        if move_type in en_passant_indices:
                            capture_moves.add(move_type)
        return capture_moves, other_moves

    def check_castling(self, orig, pieces, colors):
        orig_color = colors[orig]
        opponent_color = get_opponent_color(orig_color)
        castle_indices = set()
        if not self.king_moved[orig_color]: #king not moved yet
            for i in range(2):
                if not self.rook_moved_l_s[orig_color][i]: #check rook not moved yet
                    nr_pieces_to_rook = len(self.king_rook_l_s[orig_color][i])
                    if sum(pieces[self.king_rook_l_s[orig_color][i]]) == -nr_pieces_to_rook: #check no pieces in castle corridor
                        if all([val not in self.protected[opponent_color] for val in self.king_rook_l_s[orig_color][i]]):
                            castle_indices.add(self.rook_idx_l_s[orig_color][i])
        return castle_indices
    
    # keep track if rook/king moved for casteling
    def set_piece_moved(self, piece, color, board_idx): #0 long, 1 short
        if piece == piece_str_to_type["King"]:
            self.king_moved[color] = True
        elif piece == piece_str_to_type["Rook"]:
            if board_idx == self.rook_idx_l_s[color][0]:
                self.rook_moved_l_s[color][0] = True
            elif board_idx == self.rook_idx_l_s[color][1]:
                self.rook_moved_l_s[color][0] = True


    
