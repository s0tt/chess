import numpy as np
from misc import *
import functools
from moves import MoveGen

class Model:
    def __init__(self, view):
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
        

        self._attack_map = np.zeros(64)

        self.MoveGen = MoveGen()

        # init turn indicator
        self.player_turn = 0 #0: white, 1_ black
        self.checkmated_color = -1 #0: white, 1_ black

        self._view.draw_turn_indicator(self.player_turn)

        self.mouse_piece, self.orig = None, None
        self._last_moves = [(35,35)]
        self.allowed_moves = set()
        self.capture_moves = set()
        self.other_moves = set()
        self.pins = [[], []]
        self.checks = []


    def draw(self):
        self._view.draw(self._pieces, self._colors, self._attack_map)

    def set_piece_at_mouse(self, mouse_pos, orig, allowed_moves=None):
        board_idx = self._view.square_from_mouse(mouse_pos)
        if orig != board_idx:
            if allowed_moves != None:
                if board_idx not in allowed_moves:
                    return
            self.move_piece(orig, board_idx)

    def get_piece(self, idx):
        return self._pieces[idx]

    def get_piece_from_mouse(self, mouse_pos):
        board_idx = self._view.square_from_mouse(mouse_pos)
        return board_idx

    
    def play_move(self, orig, dest, random=False):
        allowed_moves = self.select_piece(orig)
        if not random:
            if dest in allowed_moves:
                self.move_piece(orig, dest)
        else:
            self.move_piece(orig, allowed_moves[np.random.randint(0, len(allowed_moves))])

    def move_piece(self, orig, dest):
        piece = self._pieces[orig]
        is_capture = self._pieces[dest] > 0
        if self._colors[orig] != self.player_turn:
            return
        if piece != None and dest != None:
            if dest != orig:
                if len(self.checks) > 0:
                    # check exists --> 1. move piece in way or move king if 1 check
                    if len(self.checks) == 1:
                        if piece != piece_str_to_type["King"] and dest in self.MoveGen.check_indices[0]: #move piece other than king in way
                            pass
                        # elif piece == piece_str_to_type["King"] and dest not in self.MoveGen.protected:
                        #     pass # move king out of enemy protected squares
                        elif dest  == self.checks[0]:   # capture attacking piece
                            pass
                        else:
                            self.checkmated_color = get_opponent_color(self._colors[self.checks[0]])
                            return ### CHECKMATE

                    else:
                        if piece != piece_str_to_type["King"] or dest in self.MoveGen.protected:
                            self.checkmated_color = get_opponent_color(self._colors[self.checks[0]])
                            return ### CHECKMATE

                if orig in self.pins[get_opponent_color(self.player_turn)]:
                    return
  
                # set piece type
                if piece == 1 and dest in self.capture_moves and self._pieces[dest] < 0: #  en passant
                    en_passant_piece_idx = self._last_moves[-1][1]
                    self._pieces[en_passant_piece_idx] = -1
                    self._colors[en_passant_piece_idx] = -1
                
                if piece == 4:
                    self.MoveGen.set_piece_moved(piece, self._colors[orig], orig)
                if piece == 6:
                    self.MoveGen.set_piece_moved(piece, self._colors[orig], orig)
                    if self._pieces[dest] == 4: # castling
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
                else: # normal moves
                    self._pieces[dest] = piece
                    self._pieces[orig] = -1

                    # set color
                    self._colors[dest] = self._colors[orig]
                    self._colors[orig] = -1

                # save performed move
                self._last_moves.append((orig, dest))
                self._view.set_last_move(set([orig, dest]))

                # update player turn black->white , white -> black
                self.player_turn ^= 1
                self._view.draw_turn_indicator(self.player_turn)
        self.calc_attacks()

    def calc_attacks(self):
        self._attack_map = np.zeros(64)
        self.MoveGen.reset_board_states()
        self.pins = [[],[]]
        self.checks = []
        for idx in range(self._view._board_dim**2):
            if self._pieces[idx] > 0:
                allowed_moves = self.select_piece(idx)
                if len(self.capture_moves) > 0:
                    np.put(self._attack_map, np.fromiter(self.capture_moves, int, len(self.capture_moves)), 1)

    def select_piece(self, orig):
        piece = self._pieces[orig]
        self.allowed_moves = set()
        if piece > 0:
            self.capture_moves, self.other_moves, self.pins_piece, self.checks_piece = self.MoveGen.allowed_moves(orig, piece, self._pieces, self._colors, self._last_moves[-1])
            self.pins[self._colors[orig]] += self.pins_piece
            self.checks += self.checks_piece
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
