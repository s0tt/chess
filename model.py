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
        self.MoveGen = MoveGen()
        self.mouse_piece, self.orig = None, None
        self._last_moves = []
        self._allowed_moves = set()

    def draw(self, display):
        self._view.draw(display, self._pieces, self._colors)

    def set_piece_at_mouse(self, mouse_pos, piece, orig, allowed_moves=None):
        board_idx = self._view.square_from_mouse(mouse_pos)
        if allowed_moves != None:
            if board_idx not in allowed_moves:
                return
        if piece:
            if board_idx != orig:
                # set piece type
                self._pieces[board_idx] = piece
                self._pieces[orig] = -1

                # set color
                self._colors[board_idx] = self._colors[orig]
                self._colors[orig] = -1

                # save performed move
                self._last_moves.append((orig, board_idx))

    def get_piece(self, idx):
        return self._pieces[idx]

    def get_piece_from_mouse(self, mouse_pos):
        board_idx = self._view.square_from_mouse(mouse_pos)
        piece = self._pieces[board_idx]
        if piece > 0:
            return (piece, board_idx)
        else:
            return (None, None)  # no piece there

    def handle_mouse_down(self, mouse_pos):
        self.mouse_piece, self.orig = self.get_piece_from_mouse(mouse_pos)
        if self.mouse_piece != None and self.orig != None:
            self.allowed_moves = self.MoveGen.allowed_moves(self.orig, self.mouse_piece, self._pieces, self._colors)
            self._view.change_highlights(self.allowed_moves)

    def handle_mouse_up(self, mouse_pos):
        if self.mouse_piece != None and self.orig != None:
            self.set_piece_at_mouse(mouse_pos, self.mouse_piece, self.orig, self.allowed_moves)
            self._view.change_highlights([], activate=False, all=True)
