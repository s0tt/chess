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

        self.first_rows = [[48,55], [8, 15]] #w, b pawn row indices
        self.last_rows = [[0, 7], [56,63]] #w, b pawn row indices
        self.pawn_moves = [[-8, -16], [8, 16]]
        self.pawn_captures = [[-7, -9], [7, 9]]
        self.pawn_captures64 = [[-9, -11], [9, 11]]
        self.en_passant_square_idx = None
        self.ep_cause_check_idx = set()
        self.pawn_capture_indices = set()

        self.allow_castling = [[True, True], [True, True]]
        self.allow_castling_king = True
        self.king_moved = [0, 0] # move nr in which king was moved
        self.rook_moved_l_s = [[0, 0], [0, 0]]
        self.king_rook_l_s = [[np.array([57,58, 59]), np.array([61, 62])], [np.array([1, 2, 3]), np.array([5, 6])]]
        self.rook_idx_l_s = [[56, 63], [0, 7]]
        self.castle_idx_l_s = [[58, 62], [2, 6]]
        self.king_idx = [60, 4]
        

        self.protected = [set(), set()] # protected square for both sides [white protected indices, black]
        self.check_indices = defaultdict(defaultdict(list).copy)#defaultdict(list)
        self.pin_indices = defaultdict(list)
        self.ep_check_indices = defaultdict(list)
        self.allowed_moves_piece = defaultdict(list)
        self.pins = [set(), set()] #0: white pins which black pieces, 1: vice versa
        self.checks = set()

    def check_en_passant(self, pieces, colors, last_move):
        orig, dest, _, _, _ = last_move
        if pieces[dest] == 1: # pawn moved last
            if abs(dest - orig) == abs(self.pawn_moves[0][1]): # 2 move forward
                player_col = colors[dest]
                opponent_col = get_opponent_color(player_col)
                #return set([orig, orig+self.pawn_moves[player_col][0]]), opponent_col
                #TODO: check if en passant is pinned -> would cause check
                ep_square_idx = orig+self.pawn_moves[player_col][0]
                if dest not in self.ep_check_indices or ep_square_idx in self.ep_check_indices[dest]: #check that ep doesn't cause check
                    return set([orig+self.pawn_moves[player_col][0]]), opponent_col
        return set(), None
            
    def reset_board_states(self, reset_states=True):
        self.allowed_moves_piece = defaultdict(list)
        if reset_states:
            self.check_indices = defaultdict(defaultdict(list).copy)
            self.checks = set()
            self.protected = [set(), set()]
            self.pins = [set(), set()]
            self.pin_indices = defaultdict(list)
            self.ep_check_indices = defaultdict(list)

    def allowed_moves(self, orig, piece, pieces, colors, last_move, player_turn = None):
        capture_moves = set()
        other_moves = set()
        pawn_promotions = set()
        ep_can_cause_check = []
        pin = []
        checks = []
        piece_color = colors[orig]
        if player_turn != None and player_turn != piece_color:
            return

        if piece != 1: #no pawn
            for i in range(self.offsets[piece][0]):
                idx = orig
                expand_piece_cnt = 0
                expand_piece_idx = None
                ep_check_piece_idx = None
                expanding = True
                check_in_direction = False
                all_idx = []
                last_expand_same_col = False
                while expanding or check_in_direction:
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

                            if expand_piece_cnt > 0: #>1 piece in ray
                                if pieces[idx] == piece_str_to_type["King"]:
                                    if expand_piece_cnt == 1:
                                        if expand_piece_idx != None:
                                            self.pin_indices[expand_piece_idx] = all_idx
                                            pin.append(expand_piece_idx)
                                    elif expand_piece_cnt >= 2:
                                        if ep_check_piece_idx != None:
                                            self.ep_check_indices[ep_check_piece_idx] = all_idx
                                    expanding = False
                                elif pieces[idx] == piece_str_to_type["Pawn"]:
                                    pass
                                #capture_moves.add(idx)
                                else:
                                    expanding = False
                            else: #first piece in ray
                                if pieces[idx] == piece_str_to_type["King"]:
                                    self.check_indices[all_idx[0]][0] = all_idx.copy()
                                    checks.append(all_idx[0])
                                    check_in_direction = True
                                    #expanding = False
                                # elif pieces[idx] == piece_str_to_type["Pawn"]: #enemy pawn -> ep check
                                #     ep_check_piece_idx
                                else:
                                    expand_piece_idx = idx                   
                                capture_moves.add(idx)
                        else: # field of same color
                            last_expand_same_col = True
                            if expand_piece_cnt > 0:
                                if check_in_direction:
                                    self.protected[piece_color].add(idx)
                                expanding = False
                            else:
                                if pieces[idx] == piece_str_to_type["Pawn"] and self.slide[piece]: #pawn of same color
                                    ep_check_piece_idx = idx

                                    last_expand_same_col = False
                                self.protected[piece_color].add(idx)
                        expand_piece_cnt += 1
                    else: # free space move
                        if piece == piece_str_to_type["King"]:
                            if idx in self.protected[get_opponent_color(piece_color)]:
                                    self.protected[piece_color].add(idx)
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
                if check_in_direction:
                    self.check_indices[all_idx[0]][1] = all_idx

        else:
            pawn_captures, pawn_moves, pawn_promotions, ep_indices = self.check_pawn_moves(orig, colors, pieces, last_move)
            other_moves.update(pawn_moves)
            capture_moves.update(pawn_captures)
            self.protected[piece_color].update(capture_moves)

        if orig in self.pins[get_opponent_color(piece_color)]: # check if piece is pinned by enemy
            capture_moves = set([self.pin_indices[orig][0]]).intersection(capture_moves) # capture pinning piece
            other_moves = set(self.pin_indices[orig][1:]).intersection(other_moves)

        if len(self.checks) > 0:
            # check exists
            if piece_color != colors[next(iter(self.checks))]: # only considere attacked king
                if len(self.checks) == 1:
                    check_indices_vals = self.check_indices[next(iter(self.checks))]
                    if piece != piece_str_to_type["King"]: 
                        other_moves = other_moves.intersection(check_indices_vals[0] if type(check_indices_vals[0]) == list else [check_indices_vals[0]]) #move piece other than king in way
                        
                        #capture attacking piece
                        # If king all captures are allowed as already checked for protection
                        capture_moves = set(self.checks).intersection(capture_moves)
                        # if piece == piece_str_to_type["Pawn"]:
                        #     if len(ep_indices) > 0 and next(iter(ep_indices))+self.pawn_moves[get_opponent_color(piece_color)][0] in self.checks:
                        #         # ep catpure would stop check
                        #         capture_moves.add(next(iter(ep_indices)))
                    elif piece == piece_str_to_type["King"]: #move king out to free square
                        access_idx = 1 if len(check_indices_vals) > 1 else 0
                        other_moves = other_moves - set(check_indices_vals[access_idx] if type(check_indices_vals[access_idx]) == list else [check_indices_vals[access_idx]])
                    
                    
                    # ep capture would stop check --> Piece capture
                    if piece == 1 and ep_indices != None and len(ep_indices) > 0:
                        ep_capture_field = next(iter(ep_indices))
                        ep_piece_idx_offset = -8 if piece_color == 1 else 8
                        if next(iter(self.checks)) == ep_capture_field+ep_piece_idx_offset:
                            capture_moves.add(ep_capture_field)
                        
                    # TODO: check for en passant
                else: # > 1 check
                    capture_moves = set()
                    if piece == piece_str_to_type["King"]:
                        for nr_check in self.checks:
                            access_idx = 1 if len(self.check_indices[nr_check]) > 1 else 0
                            other_moves = other_moves - set(self.check_indices[nr_check][access_idx] if type(self.check_indices[nr_check][access_idx]) == list else [self.check_indices[nr_check][access_idx]]) # find if free unchecked square exists
            else:
                capture_moves = set()
                other_moves = set()    
        #self.allowed_moves = self.capture_moves.union(self.other_moves)

        # integrate promotion indices into move sets
        if len(pawn_promotions) > 0:
            promotion_indices = set()
            for promotion_move in pawn_promotions:
                dest, move_type = promotion_move
                promotion_indices.add(dest)
                is_capture = move_type & 0b0100 
                if is_capture:
                    if dest in capture_moves:
                        capture_moves.add(promotion_move)
                else:
                    if dest in other_moves:
                        other_moves.add(promotion_move)
            for idx in promotion_indices:
                if idx in capture_moves:
                    capture_moves.remove(idx)      
                if idx in other_moves:    
                    other_moves.remove(idx)            

        self.allowed_moves_piece[orig] = capture_moves.union(other_moves)
        if len(pin) > 0:
            self.pins[piece_color].add(pin[0])
        if len(checks) > 0:
            self.checks.add(checks[0])
        if len(ep_can_cause_check) > 0:
            self.ep_cause_check_idx.add()

        return capture_moves, other_moves
    
    def promotion_moves(self, dest, capture=False):
        add_bitmask = 0b0100 if capture else 0b0000
        promo_n = move_types["promo_n"] | add_bitmask
        promo_b = move_types["promo_b"] | add_bitmask
        promo_r = move_types["promo_r"] | add_bitmask
        promo_q = move_types["promo_q"] | add_bitmask
        return [(dest,promo_n), (dest,promo_b), (dest,promo_r), (dest,promo_q)]

    def check_pawn_moves(self, orig, colors, pieces, last_move):
        orig_color = colors[orig]
        capture_moves = set()
        other_moves = set()
        promotion_move = set()
        move_1_fwrd = orig+self.pawn_moves[orig_color][0]
        move_2_fwrd = orig+self.pawn_moves[orig_color][1]
        move_l_cptr = orig+self.pawn_captures[orig_color][0]
        move_r_cptr = orig+self.pawn_captures[orig_color][1]
                
        if pieces[move_1_fwrd] < 0: # check free space
            if self.last_rows[orig_color][0] <= move_1_fwrd <= self.last_rows[orig_color][1]:
                promotion_move.update(self.promotion_moves(move_1_fwrd))
            other_moves.add(move_1_fwrd)
            if self.first_rows[orig_color][0] <= orig <= self.first_rows[orig_color][1]: # case 2 moves allowed from 1st row
                if pieces[move_2_fwrd] < 0:
                    other_moves.add(move_2_fwrd)
            
        
        # check captures with board boundaries
        en_passant_color = None
        en_passant_indices = set()
        valid_en_passant_indices = set()
        pawn_protected = set()
        self.pawn_capture_indices = set()
        for move_idx, move_type in zip([0, 1],[move_l_cptr, move_r_cptr]):
            new_idx = self.mailbox[self.mailbox64[orig]+self.pawn_captures64[orig_color][move_idx]]
            if new_idx > -1:
                self.protected[orig_color].add(new_idx)
                if colors[move_type]  == get_opponent_color(orig_color): #field is enemy field
                    if pieces[new_idx] == piece_str_to_type["King"]:# Pawn checks
                        self.check_indices[orig] = [orig]
                        self.checks.add(orig)
                    else:
                        # capture promotion
                        if self.last_rows[orig_color][0] <= move_type <= self.last_rows[orig_color][1]:
                            promotion_move.update(self.promotion_moves(move_type, capture=True))
                        
                        capture_moves.add(move_type)
                else:
                    if en_passant_color is None:
                        en_passant_indices, en_passant_color = self.check_en_passant(pieces, colors, last_move)
                    if en_passant_color == orig_color:
                        if move_type in en_passant_indices:
                            if orig not in self.pins[get_opponent_color(orig_color)] or move_type in self.pin_indices[orig]:#check that ep is pinned -> doesn't cause check
                                capture_moves.add(move_type)
                                valid_en_passant_indices.add(move_type)
        return capture_moves, other_moves, promotion_move, valid_en_passant_indices

    def check_castling(self, orig, pieces, colors):
        orig_color = colors[orig]
        opponent_color = get_opponent_color(orig_color)
        castle_indices = set()
        if not self.king_moved[orig_color] and pieces[self.king_idx[orig_color]] == piece_str_to_type["King"]: #king not moved yet
            if len(self.checks) > 0 and colors[next(iter(self.checks))] == opponent_color:
                return castle_indices # if check of same color king is present -> no
            for i in range(2):
                if pieces[self.rook_idx_l_s[orig_color][i]] == piece_str_to_type["Rook"]: #check rook exists
                    if not self.rook_moved_l_s[orig_color][i]: #check rook not moved yet
                        nr_pieces_to_rook = len(self.king_rook_l_s[orig_color][i])
                        if sum(pieces[self.king_rook_l_s[orig_color][i]]) == -nr_pieces_to_rook: #check no pieces in castle corridor
                            if all([val not in self.protected[opponent_color] for val in self.king_rook_l_s[orig_color][i][abs(i-1):]]):
                                #castle_indices.add(self.rook_idx_l_s[orig_color][i])
                                castle_indices.add(self.castle_idx_l_s[orig_color][i])
                                
        return castle_indices
    
    # keep track if rook/king moved for casteling
    def set_piece_moved(self, piece, color, board_idx, move_nr): #0 long, 1 short
        if piece == piece_str_to_type["King"] and self.king_moved[color] == 0:
            self.king_moved[color] = move_nr
        elif piece == piece_str_to_type["Rook"]:
            if board_idx == self.rook_idx_l_s[color][0] and self.rook_moved_l_s[color][0] == 0:
                self.rook_moved_l_s[color][0] = move_nr
            elif board_idx == self.rook_idx_l_s[color][1] and self.rook_moved_l_s[color][1] == 0:
                self.rook_moved_l_s[color][1] = move_nr

    def reset_pieces_moved(self, move_nr, color):
        if self.king_moved[color] == move_nr and self.allow_castling_king:
            self.king_moved[color] = 0 
        if self.rook_moved_l_s[color][0] == move_nr and self.allow_castling[color][0]:
            self.rook_moved_l_s[color][0] = 0             
        if self.rook_moved_l_s[color][1] == move_nr and self.allow_castling[color][1]:
            self.rook_moved_l_s[color][1] = 0



    
