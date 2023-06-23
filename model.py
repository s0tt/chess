import numpy as np
from misc import *
import functools
from moves import MoveGen
from view import Board
from collections import defaultdict


class Model:
    """Model according to MVC pattern representing internal board data states.
        Handles everything from board arrangment of pieces/colors, nr of moves, player turns, FEN string handling etc.
    """
    def __init__(self, view : Board, board_dim=8, sounds=True, fen_init=""):
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
        self._sounds = sounds
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

        self.last_board_state_diff = {}  # tracks diff to last before state before last move
        self._board_dim = board_dim
        self._attack_map = np.zeros(64)
        self._old_pieces = self._pieces
        self._old_colors = self._colors

        self.MoveGen = MoveGen()

        # init turn indicator
        self.player_turn = 0  # 0: white, 1_ black
        self.checkmated_color = -1  # 0: white, 1_ black
        self.move_nr = 1
        self.half_moves_50_check = 0

        self.mouse_piece, self.orig = None, None
        self._last_moves = [(35, 35, False, -1, -1)] # Tuple of: orig, dest, move_type, old_piece, old_color
        self.allowed_moves = set()

        self.capture_moves = set()
        self.other_moves = set()
        self.promotion_moves = set()

        self.piece_counts = {1: [8, 8], 2: [2, 2], 3: [2, 2], 4: [2, 2], 5: [1, 1], 6: [1, 1]}
        self.nr_allowed_moves = []

        if len(fen_init) > 0:
            self.set_fen_string(fen_init)

    def draw(self):
        if self._view != None:
            self._view.draw(self._pieces, self._colors, self._attack_map)

    def eval_board_shannon(self, nr_legal_moves):
        turn = self.player_turn
        enemy = get_opponent_color(turn)
        score = 0
        if self.checkmated_color > 0:
            score += 200*( 1 if turn != self.checkmated_color else -1)
        score += 9 * (self.piece_counts[piece_str_to_type["Queen"]][turn] - self.piece_counts[piece_str_to_type["Queen"]][enemy])
        score += 5 * (self.piece_counts[piece_str_to_type["Rook"]][turn] - self.piece_counts[piece_str_to_type["Rook"]][enemy])
        score += 3 * (self.piece_counts[piece_str_to_type["Bishop"]][turn] - self.piece_counts[piece_str_to_type["Bishop"]][enemy])
        score += 3 * (self.piece_counts[piece_str_to_type["Knight"]][turn] - self.piece_counts[piece_str_to_type["Knight"]][enemy])
        score += 1 * (self.piece_counts[piece_str_to_type["Pawn"]][turn] - self.piece_counts[piece_str_to_type["Pawn"]][enemy])
        # TODO: double blocked and isolated pawn
        #score -= 0.5 * (self.piece_counts[piece_str_to_type["Knight"]][turn] - self.piece_counts[piece_str_to_type["Knight"]][enemy])

        score += 0.1 * (self.nr_allowed_moves[turn]-self.nr_allowed_moves[enemy])
        return score

    def count_piece_changes(self, player_color, old_piece, move_type, move_dir="move"):
        enemy_color = get_opponent_color(player_color)
        change = 1 if move_dir == "move" else -1
        if move_type & 0b0100: #capture
            if move_type == move_types["ep_capture"]:
                self.piece_counts[piece_str_to_type["Pawn"]][enemy_color] -= change
            else:
                self.piece_counts[old_piece][enemy_color] -= change
        if move_type & 0b1000: #promotion
            new_piece = move_promo_to_piece[move_type]
            self.piece_counts[new_piece][player_color] += change
            self.piece_counts[piece_str_to_type["Pawn"]][player_color] -= change
            



    def set_piece_at_mouse(self, mouse_pos, orig, allowed_moves=None):
        board_idx = self._view.square_from_mouse(mouse_pos)
        indices = np.array(
            [i[0] if type(i) == tuple else i for i in allowed_moves])
        types = np.array(
            [i[1] if type(i) == tuple else i for i in allowed_moves])
        board_idx_pos = np.where(indices == board_idx)
        if orig != board_idx:
            if allowed_moves != None:
                if len(board_idx_pos[0]) <= 0:
                    return
                else:
                    selected_move_idx = np.random.choice(board_idx_pos[0])
                if any(types != indices):
                    self.move_piece_checked(
                        orig, (indices[selected_move_idx], types[selected_move_idx]))
                else:
                    self.move_piece_checked(orig, indices[selected_move_idx])

    def get_piece(self, idx):
        return self._pieces[idx]

    def get_piece_from_mouse(self, mouse_pos):
        board_idx = self._view.square_from_mouse(mouse_pos)
        return board_idx

    def get_fen_string(self):
        fen_string = ""
        empty_fields = 0
        for row in range(self._board_dim):
            for col in range(self._board_dim):
                i = grid2continous(row, col)
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
                if not self.MoveGen.rook_moved_l_s[i][1]:
                    castling_string += "K" if i == 0 else "k"
                if not self.MoveGen.rook_moved_l_s[i][0]:
                    castling_string += "Q" if i == 0 else "q"
        fen_string += castling_string if len(castling_string) > 0 else "-"
        en_passant_indices, _ = self.MoveGen.check_en_passant(
            self._pieces, self._colors, self._last_moves[-1])
        fen_string += " " + self.board2alphanum(next(iter(en_passant_indices))) if (
            len(en_passant_indices)) > 0 else " -"
        fen_string += " " + str(self.half_moves_50_check)
        fen_string += " " + str(self.move_nr)
        return fen_string

    def set_fen_string(self, fen_string):
        str_parts = fen_string.split(" ")
        self.piece_counts = {}
        game_string = str_parts[0].replace("/", "")
        empty_cnt = 0
        i = 0
        for idx in range(self._board_dim**2):
            self._pieces[idx] = -1
            self._colors[idx] = -1
            if empty_cnt > 0:
                empty_cnt -= 1
                continue
            if game_string[i].isnumeric():
                empty_cnt = int(game_string[i])-1
            else:
                piece = fen_codec[game_string[i].lower(
                )] if game_string[i].lower() in fen_codec else -1
                self._pieces[idx] = piece
                self._colors[idx] = 0 if game_string[i].isupper() else 1
                self.piece_counts[piece][self._colors[idx]] += 1
            i += 1

        self.player_turn = 0 if str_parts[1] == "w" else 1
        # castling
        self.MoveGen.rook_moved_l_s[1][1] = 1 if "k" not in str_parts[2] else 0
        self.MoveGen.rook_moved_l_s[1][0] = 1 if "q" not in str_parts[2] else 0
        self.MoveGen.rook_moved_l_s[0][1] = 1 if "K" not in str_parts[2] else 0
        self.MoveGen.rook_moved_l_s[0][0] = 1 if "Q" not in str_parts[2] else 0

        self.MoveGen.allow_castling[1][1] = False if "k" not in str_parts[2] else True
        self.MoveGen.allow_castling[1][0] = False if "q" not in str_parts[2] else True
        self.MoveGen.allow_castling[0][1] = False if "K" not in str_parts[2] else True
        self.MoveGen.allow_castling[0][0] = False if "Q" not in str_parts[2] else True

        if "-" in str_parts[2]:
            self.MoveGen.allow_castling_king = False
            self.MoveGen.king_moved = [1, 1]
        else:
            self.MoveGen.allow_castling_king = True
            self.MoveGen.king_moved = [0, 0]

        # en passant (ep)
        if str_parts[3] != "-":
            # reproduce last move from ep alphanum
            idx = self.alphanum2board(str_parts[3])
            if idx > 32:  # white side ep
                last_move = (idx+self._board_dim, idx-self._board_dim,
                             move_types["pawn_double"], -1, -1)
            else:  # black side ep
                last_move = (idx-self._board_dim, idx+self._board_dim,
                             move_types["pawn_double"], -1, -1)
            self._last_moves.append((last_move))
        self.half_moves_50_check = int(str_parts[4])
        self.move_nr = int(str_parts[5])

    def board2alphanum(self, idx):
        row, col = continous2grid(idx)
        alphabetic = "abcdefgh"
        nums = "87654321"
        return alphabetic[col]+nums[row]

    def alphanum2board(self, alphanum):
        alphabetic = "abcdefgh"
        nums = "87654321"
        col = alphabetic.index(alphanum[0])
        row = nums.index(alphanum[1])
        return grid2continous(row, col)

    def play_move(self, orig, dest, random=False):
        allowed_moves = self.select_piece(orig)
        if not random:
            if dest in allowed_moves:
                self.move_piece_checked(orig, dest)
        else:
            self.move_piece_checked(
                orig, allowed_moves[np.random.randint(0, len(allowed_moves))])

    def move_piece_checked(self, orig, dest):
        if self._colors[orig] != self.player_turn:
            return
        self.move_piece(orig, dest)
        self.calc_attacks()
        if len(self.MoveGen.checks) > 0:
            self.play_sound("check")
        return 0

    def move_piece(self, orig, move, silent=False):  # unchecked physical board move
        if type(move) == tuple:
            dest, move_type = move
            is_capture = move_type & 0b0100  # self._pieces[dest] > 0
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
                    self.MoveGen.set_piece_moved(
                        piece, self._colors[orig], orig, self.move_nr)
                if piece == 6:
                    self.MoveGen.set_piece_moved(
                        piece, self._colors[orig], orig, self.move_nr)
                    # if self._pieces[dest] == 4:  # castling
                    if orig == self.MoveGen.king_idx[piece_col] and dest in self.MoveGen.castle_idx_l_s[piece_col]:
                        is_capture = False
                        is_castling = True
                        # set rook moved state

                        self.play_sound("castle", silent)
                        # long castle
                        if dest == self.MoveGen.castle_idx_l_s[piece_col][0]:
                            move_type = move_types["castle_queen"]
                            self._pieces[orig-2] = 6
                            self._pieces[orig-1] = 4
                            self._colors[orig-2] = self._colors[orig]
                            self._colors[orig-1] = self._colors[orig]
                            self._colors[orig-4] = -1
                            self._pieces[orig-4] = -1
                            self.MoveGen.set_piece_moved(
                                4, piece_col, self.MoveGen.rook_idx_l_s[piece_col][0], self.move_nr)
                        # short castle
                        elif dest == self.MoveGen.castle_idx_l_s[piece_col][1]:
                            move_type = move_types["castle_king"]
                            self._pieces[orig+2] = 6
                            self._pieces[orig+1] = 4
                            self._colors[orig+2] = self._colors[orig]
                            self._colors[orig+1] = self._colors[orig]
                            self._colors[orig+3] = -1
                            self._pieces[orig+3] = -1
                            self.MoveGen.set_piece_moved(
                                4, piece_col, self.MoveGen.rook_idx_l_s[piece_col][1], self.move_nr)
                        old_col = self._colors[orig]
                        self._colors[orig] = -1
                        self._pieces[orig] = -1

                if piece == 1:
                    # #pawn promotion
                    if is_promotion and move_type != None:
                        self.play_sound("promote", silent)
                        self._pieces[dest] = move_promo_to_piece[move_type]
                        self._pieces[orig] = -1

                        # set color
                        if not move_type & 0b0100:  # if not is capture
                            old_col = self._colors[orig]
                        self._colors[dest] = self._colors[orig]
                        self._colors[orig] = -1

                    # en passant
                    if abs(orig-dest) != 8 and abs(orig-dest) != 16 and self._pieces[dest] < 0:
                        en_passant_piece_idx = self._last_moves[-1][1]
                        self._pieces[en_passant_piece_idx] = -1
                        old_col = self._colors[en_passant_piece_idx]
                        self._colors[en_passant_piece_idx] = -1
                        is_capture = True
                        move_type = move_types["ep_capture"]
                if not is_castling and not is_promotion:  # normal moves
                    self._pieces[dest] = piece
                    self._pieces[orig] = -1

                    # set color
                    self._colors[dest] = self._colors[orig]
                    self._colors[orig] = -1

                    # call sound making
                    self.play_sound("capture" if is_capture else "move", silent)

                # save performed move
                last_move_type = move_types["quiet"]
                if move_type != None:
                    last_move_type = move_type
                elif is_capture:
                    last_move_type = move_types["capture"]
                    # if is capture of rook check castling compromised or still possible
                self.count_piece_changes(piece_col, old_piece, last_move_type, move_dir="move")
                self._last_moves.append(
                    (orig, dest, last_move_type, old_piece, old_col))
                if self._view is not None and not silent:
                    self._view.set_last_move(set([orig, dest]))

                # update player turn black->white , white -> black
                self.move_nr += 1 if self.player_turn == 1 else 0
                self.player_turn ^= 1
                if (piece == 1 or is_capture or is_castling):
                    self.old_moves_50_check = self.half_moves_50_check
                    self.half_moves_50_check = 0
                else:
                    self.half_moves_50_check += 1

    def play_sound(self, sound_type, silent=False):
        if self._view != None and self._sounds == True and not silent:
            self._view.play_sound(sound_type)

    def print_board_state(self, orig=None, dest=None):
        if not orig or not dest:
            orig, dest, move_type, old_piece, old_col = self._last_moves[-1]
        print_board_string(orig, dest, self._pieces, self._colors)

    def unmove_piece(self):
        self.player_turn = get_opponent_color(self.player_turn)
        self.move_nr -= 1 if self.player_turn == 1 else 0
        orig, dest, move_type, old_piece, old_col = self._last_moves.pop()

        if move_type & 0b0100:  # is_capture
            # replace captured piece
            if move_type & 0b1000:  # is_promotion
                # replace pawn back
                self._pieces[orig] = 1  # pawn
            else:
                # move other piece back
                self._pieces[orig] = self._pieces[dest]
            self._colors[orig] = self._colors[dest]
            if move_type == move_types["ep_capture"]:
                ep_piece_offset = -8 if old_col == 0 else 8
                self._colors[dest] = -1
                self._pieces[dest] = -1
                self._colors[dest+ep_piece_offset] = old_col
                self._pieces[dest+ep_piece_offset] = piece_str_to_type["Pawn"]
            else:
                self._colors[dest] = old_col
                self._pieces[dest] = old_piece

        elif move_type & 0b1000:  # is_promotion
            self._colors[orig] = old_col
            self._pieces[orig] = 1
            self._colors[dest] = -1
            self._pieces[dest] = -1
        elif move_type == 2 or move_type == 3:  # castling
            if move_type == 3:  # long castle
                self._pieces[orig-2] = -1
                self._pieces[orig-1] = -1
                self._colors[orig-2] = -1
                self._colors[orig-1] = -1
                self._colors[orig-4] = old_col
                self._pieces[orig-4] = 4
            elif move_type == 2:  # short castle king side
                self._pieces[orig+2] = -1
                self._pieces[orig+1] = -1
                self._colors[orig+2] = -1
                self._colors[orig+1] = -1
                self._colors[orig+3] = old_col
                self._pieces[orig+3] = 4
            self._colors[orig] = old_col
            self._pieces[orig] = 6

        else:  # normal
            self._colors[orig] = self._colors[dest]
            self._pieces[orig] = self._pieces[dest]
            self._colors[dest] = -1
            self._pieces[dest] = -1

        # reset moved states if
        self.MoveGen.reset_pieces_moved(self.move_nr, self._colors[orig])

        self.count_piece_changes(self._colors[orig], old_piece, move_type, move_dir="unmove")

        if (self._pieces[orig] == 1 or move_type & 0b0100 or move_type == 2 or move_type == 3):
            # assert self.half_moves_50_check == 0
            self.half_moves_50_check = self.old_moves_50_check
        else:
            # assert self.half_moves_50_check > 0
            self.half_moves_50_check -= 1

    def calc_attacks(self, silent=False):
        for i, true_val in enumerate([True, False]):
            move_possible = [False, False]
            self._attack_map = np.zeros(64)
            self.MoveGen.reset_board_states(true_val)
            for idx in range(self._board_dim**2):
                piece_color = self._colors[idx]
                if self._pieces[idx] > 0:
                    legal_moves = self.select_piece(idx)
                    move_possible[piece_color] |= (len(legal_moves) > 0)
            if i == 1:
                self.analyse_checkmate(move_possible, silent)

    def generate_legal_moves(self, color=None, silent=False):
        self.calc_attacks(silent=silent)
        self.nr_allowed_moves = []
        for key in list(self.MoveGen.allowed_moves_piece.keys()).copy():
            # check if move is players turn
            if self.player_turn != self._colors[key] and color != None:
                self.nr_allowed_moves[self._colors[key]] += 1
                del self.MoveGen.allowed_moves_piece[key]
            else:
                self.nr_allowed_moves[self.player_turn] += 1
        
        return self.MoveGen.allowed_moves_piece

    def analyse_checkmate(self, move_possible, silent):
        if len(self.MoveGen.checks) > 0 and not move_possible[self.player_turn]:
            # no legal moves for player that got checked left --> MATE
            self.checkmated_color = self.player_turn
            self.play_sound("checkmate", silent)

    def select_piece(self, orig, check_turn=False):
        piece = self._pieces[orig]
        self.allowed_moves = set()
        if check_turn and self._colors[orig] != self.player_turn:
            return self.allowed_moves
        if piece > 0:
            self.capture_moves, self.other_moves = self.MoveGen.allowed_moves(
                orig, piece, self._pieces, self._colors, self._last_moves[-1])
            self.allowed_moves = self.capture_moves.union(self.other_moves)
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
