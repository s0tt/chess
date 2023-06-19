import numpy as np
from misc import *
import functools
from moves import MoveGen

class Model:
    def __init__(self, view, board_dim=8, fen_init="rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8"):
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
        self._view = view
        self._colors = np.array([1, 1, 1, 1, 1, 1, 1, 1,
                                 1, 1, 1, 1, 1, 1, 1, 1,
                                 -1, -1, -1, -1, -1, -1, -1, -1,
                                 -1, -1, -1, -1, -1, -1, -1, -1,
                                 -1, -1, -1, -1, -1, -1, -1, -1,
                                 -1, -1, -1, -1, -1, -1, -1, -1,
                                 0, 0, 0, 0, 0, 0, 0, 0,
                                 0, 0, 0, 0, 0, 0, 0, 0])

        # 1: "Pawn", 2: "Knight", 3: "Bishop", 4: "Rook", 5: "Queen", 6: "King"
        self._pieces = np.array([4, 2, 3, 5, 6, 3, 2, 4,
                                 1, 1, 1, 1, 1, 1, 1, 1,
                                 -1, -1, -1, -1, -1, -1, -1, -1,
                                 -1, -1, -1, -1, -1, -1, -1, -1,
                                 -1, -1, -1, -1, -1, -1, -1, -1,
                                 -1, -1, -1, -1, -1, -1, -1, -1,
                                 1, 1, 1, 1, 1, 1, 1, 1,
                                 4, 2, 3, 5, 6, 3, 2, 4])
        
        self.last_board_state_diff = {} # tracks diff to last before state before last move
        self._board_dim = board_dim
        self._attack_map = np.zeros(64)
        self._old_pieces = self._pieces
        self._old_colors = self._colors

        self.MoveGen = MoveGen()

        # init turn indicator
        self.player_turn = 0 #0: white, 1_ black
        self.checkmated_color = -1 #0: white, 1_ black
        self.move_nr = 1
        self.half_moves_50_check = 0

        self.mouse_piece, self.orig = None, None
        self._last_moves = [(35,35, False, -1, -1)]
        self.allowed_moves = set()

        self.capture_moves = set()
        self.other_moves = set()
        self.promotion_moves = set()
        # self.pins = [[], []]
        # self.checks = []
        if len(fen_init) > 0:
            self.set_fen_string(fen_init)


    def draw(self):
        if self._view != None:
            self._view.draw(self._pieces, self._colors, self._attack_map)

    def set_piece_at_mouse(self, mouse_pos, orig, allowed_moves=None):
        board_idx = self._view.square_from_mouse(mouse_pos)
        indices = np.array([i[0] if type(i) == tuple else i for i in allowed_moves])
        types = np.array([i[1] if type(i) == tuple else i for i in allowed_moves])
        board_idx_pos = np.where(indices == board_idx)
        if orig != board_idx:
            if allowed_moves != None:
                if len(board_idx_pos[0]) <= 0:
                    return
                else:
                    selected_move_idx = np.random.choice(board_idx_pos[0])   
                if any(types != indices):           
                    self.move_piece_checked(orig, (indices[selected_move_idx], types[selected_move_idx]))
                else:
                    self.move_piece_checked(orig, indices[selected_move_idx])
    def get_piece(self, idx):
        return self._pieces[idx]

    def get_piece_from_mouse(self, mouse_pos):
        board_idx = self._view.square_from_mouse(mouse_pos)
        return board_idx

    def get_fen_string(self):
        fen_codec_reverse = {v: k for k, v in fen_codec.items()}
        fen_string = ""
        empty_fields = 0
        for row in range(self._board_dim):
            for col in range(self._board_dim):
                i = grid2continous(row,col)
                if self._pieces[i] < 0:
                    empty_fields += 1
                    continue
                else:
                    if empty_fields > 0:
                        fen_string += str(empty_fields)
                        empty_fields = 0
                    fen_letter = str(fen_codec_reverse[self._pieces[i]])
                    if self._colors[i] == 0:
                        fen_letter = fen_letter.upper()
                    fen_string += fen_letter
                
            fen_string += str(empty_fields) if empty_fields > 0 else ""
            empty_fields = 0
            fen_string += "/" if row != self._board_dim-1 else ""
        fen_string += " w " if self.player_turn == 0 else " b "
        castling_string = ""
        for i in range(2):
            if not self.MoveGen.king_moved[i]:
                if self.MoveGen.rook_moved_l_s[1]:
                    castling_string += "K" if i == 0 else "k"
                if self.MoveGen.rook_moved_l_s[0]:
                    castling_string += "Q" if i == 0 else "q"
        fen_string += castling_string if len(castling_string) > 0 else "-"
        en_passant_indices, _ = self.MoveGen.check_en_passant(self._pieces,self._colors, self._last_moves[-1])
        fen_string += " " + self.get_alpha_num_square(en_passant_indices[0]) if (en_passant_indices != None and len(en_passant_indices)) > 0 else " -"
        fen_string += " " + str(self.half_moves_50_check)
        fen_string += " " + str(self.move_nr)
        return fen_string

    def set_fen_string(self, fen_string):
        str_parts = fen_string.split(" ")
        game_string = str_parts[0].replace("/", "")
        empty_cnt = 0
        i = 0
        for idx in range(self._board_dim**2):
            self._pieces[idx] = -1
            self._colors[idx] = -1
            if empty_cnt > 0:
                empty_cnt-= 1
                continue
            if game_string[i].isnumeric():
                empty_cnt = int(game_string[i])-1
            else:
                piece = fen_codec[game_string[i].lower()] if game_string[i].lower() in fen_codec else -1
                self._pieces[idx] = piece
                self._colors[idx] = 0 if game_string[i].isupper() else 1
            i += 1

                
        self.player_turn = 0 if str_parts[1] == "w" else 1
        # castling
        if "k" in str_parts[2]:
            self.MoveGen.rook_moved_l_s[1][1]
        if "q" in str_parts[2]:
            self.MoveGen.rook_moved_l_s[1][0]
        if "K" in str_parts[2]:
            self.MoveGen.rook_moved_l_s[0][1]
        if "Q" in str_parts[2]:
            self.MoveGen.rook_moved_l_s[0][0]
        if "-" in str_parts[2]:
            self.king_moved = True

        #en passant (ep)
        if str_parts[3] != "-"

        else:
            

        self.half_moves_50_check = int(str_parts[4])
        self.move_nr = int(str_parts[5])
            

    def get_alpha_num_square(self, idx):
        row, col = continous2grid(idx)
        alphabetic = "abcdefgh"
        nums = "87654321"
        return alphabetic[col]+nums[row]
    
    def play_move(self, orig, dest, random=False):
        allowed_moves = self.select_piece(orig)
        if not random:
            if dest in allowed_moves:
                self.move_piece_checked(orig, dest)
        else:
            self.move_piece_checked(orig, allowed_moves[np.random.randint(0, len(allowed_moves))])


    def move_piece_checked(self, orig, dest):
        if self._colors[orig] != self.player_turn:
            return
        self.move_piece(orig, dest)
        self.calc_attacks()
        if len(self.MoveGen.checks) > 0:
            self.play_sound("check")
        return 0

    def move_piece(self, orig, move): #unchecked physical board move
        if type(move) == tuple:
            dest, move_type = move
            is_capture = move_type & 0b0100 #self._pieces[dest] > 0
            is_promotion = move_type & 0b1000
        else:
            dest = move
            move_type = None
            is_capture = self._pieces[dest] > 0
            is_promotion = False
        piece = self._pieces[orig]
        is_castling = False
        old_piece = self._pieces[dest]
        old_col = self._colors[dest]
        piece_col = self._colors[orig]
        if piece != None and dest != None:
            if dest != orig:
                # set piece type
                if piece == 4:
                    self.MoveGen.set_piece_moved(piece, self._colors[orig], orig)
                if piece == 6:
                    self.MoveGen.set_piece_moved(piece, self._colors[orig], orig)
                    if self._pieces[dest] == 4: # castling
                        is_castling = True
                        self.play_sound("castle")
                        if abs(orig - dest) == 4: #long castle
                            self._pieces[orig-2] = 6
                            self._pieces[orig-1] = 4
                            self._colors[orig-2] = self._colors[orig]
                            self._colors[orig-1] = self._colors[orig]
                        else: #short castle
                            self._pieces[orig+2] = 6
                            self._pieces[orig+1] = 4
                            self._colors[orig+2] = self._colors[orig]
                            self._colors[orig+1] = self._colors[orig]
                        self._colors[orig] = -1
                        self._colors[dest] = -1
                        self._pieces[orig] = -1
                        self._pieces[dest] = -1 

                if piece == 1:
                    # #pawn promotion
                    if is_promotion and move_type != None:
                        self.play_sound("promote")
                        self._pieces[dest] = move_promo_to_piece[move_type]
                        self._pieces[orig] = -1

                        # set color
                        self._colors[dest] = self._colors[orig]
                        self._colors[orig] = -1

                    # if self.MoveGen.last_rows[piece_col][0] <= dest <= self.MoveGen.last_rows[piece_col][1]:
                    #     self._pieces[dest] = promote_piece
                    if dest in self.capture_moves and self._pieces[dest] < 0: #  en passant
                        en_passant_piece_idx = self._last_moves[-1][1]
                        self._pieces[en_passant_piece_idx] = -1
                        self._colors[en_passant_piece_idx] = -1
                if not is_castling and not is_promotion: # normal moves
                    self._pieces[dest] = piece
                    self._pieces[orig] = -1

                    # set color
                    self._colors[dest] = self._colors[orig]
                    self._colors[orig] = -1

                    # call sound making
                    self.play_sound("capture" if is_capture else "move")

                    # if dest in self.MoveGen.pins[self._colors[dest]]:
                    #     # recalc attacks after capture check
                    #     reset_check = False
                    #     self.calc_attacks()

                # save performed move
                last_move_type = move_types["quiet"]
                if move_type != None:
                    last_move_type = move_type 
                elif is_capture:
                    last_move_type = move_types["capture"]
                self._last_moves.append((orig, dest, last_move_type, old_piece, old_col))
                if self._view is not None:
                    self._view.set_last_move(set([orig, dest]))

                # update player turn black->white , white -> black
                self.move_nr += 1 if self.player_turn == 1 else 0
                self.player_turn ^= 1
                self.half_moves_50_check = 0 if (piece == 1 or is_capture) else self.half_moves_50_check+1
    
    def play_sound(self, sound_type):
        if self._view != None:
            self._view.play_sound(sound_type)

    def unmove_piece(self):
        self.player_turn = get_opponent_color(self.player_turn)
        self.move_nr -= 1 if self.player_turn == 1 else 0
        orig, dest, move_type, old_piece, old_col = self._last_moves.pop()
        self.half_moves_50_check -= 1


        if move_type & 0b0100: #is_capture
            # replace captured piece
            if move_type & 0b1000: #is_promotion
                # replace pawn back
                self._pieces[orig] = 1 #pawn               
            else:
                # move other piece back
                self._pieces[orig] = self._pieces[dest]
            self._colors[orig] = self._colors[dest]
            self._colors[dest] = old_col
            self._pieces[dest] = old_piece

        elif move_type & 0b1000: #is_promotion
            self._colors[orig] = old_col
            self._pieces[orig] = old_piece
            self._colors[dest] = -1
            self._pieces[dest] = -1
        else: #normal
            self._colors[orig] = self._colors[dest]
            self._pieces[orig] = self._pieces[dest]
            self._colors[dest] = -1
            self._pieces[dest] = -1

    def calc_attacks(self):
        for i, true_val in enumerate([True, False]):
            move_possible = [False, False]
            self._attack_map = np.zeros(64)
            self.MoveGen.reset_board_states(true_val)
            # self.pins = [[],[]]
            # self.checks = []
            for idx in range(self._board_dim**2):
                piece_color = self._colors[idx]
                if self._pieces[idx] > 0:
                    legal_moves = self.select_piece(idx)
                    move_possible[piece_color] |= (len(legal_moves) > 0)
                    #if len(self.capture_moves) > 0:
                        #np.put(self._attack_map, np.fromiter(self.capture_moves, int, len(self.capture_moves)), 1)
            if i == 1:
                self.analyse_checkmate(move_possible)

    def generate_legal_moves(self):
        self.calc_attacks()
        return self.MoveGen.allowed_moves_piece

    def analyse_checkmate(self, move_possible):
        if len(self.MoveGen.checks) > 0 and not move_possible[self.player_turn]:
            # no legal moves for player that got checked left --> MATE
            self.checkmated_color = self.player_turn
            self.play_sound("checkmate")

    def select_piece(self, orig, check_turn=False):
        piece = self._pieces[orig]
        self.allowed_moves = set()
        if check_turn and self._colors[orig] != self.player_turn:
            return self.allowed_moves
        if piece > 0:
            self.capture_moves, self.other_moves  = self.MoveGen.allowed_moves(orig, piece, self._pieces, self._colors, self._last_moves[-1])
            self.allowed_moves =  self.capture_moves.union(self.other_moves)
        return self.allowed_moves


    def handle_mouse_down(self, mouse_pos):
        self.orig = self.get_piece_from_mouse(mouse_pos)
        if self.orig != None:
            allowed_moves = self.select_piece(self.orig)
            self._view.change_highlights(allowed_moves)

    def handle_mouse_up(self, mouse_pos):
        if self.orig != None:
            self.set_piece_at_mouse(mouse_pos, self.orig, self.allowed_moves)
            self._view.change_highlights([], activate=False, all=True)
