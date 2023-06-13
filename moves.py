import numpy as np
from misc import *

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
        #self.all_allowed_moves = []

    #@functools.lru_cache(maxsize=128)
    def allowed_moves(self, orig, piece, pieces, colors):
        moves = set()
        if piece != 1: #no pawn
            for i in range(self.offsets[piece][0]):
                idx = orig
                expanding = True
                while expanding:
                    idx = self.mailbox[self.mailbox64[idx] + self.offsets[piece][1][i]]
                    if idx == -1:
                        break
                    if pieces[idx] >= 0:
                        if colors[orig] != colors[idx]:
                            # enemy field capture
                            #if piece == piece_str_to_type("King"):
                                # TODO check if to captured piece is protected
                                #pass
                            moves.add(idx)
                            expanding = False
                        else:
                            expanding = False
                    else:
                        moves.add(idx)
                        if not self.slide[piece]:
                            expanding = False
        else:
            #pawn moves for white pawns
            orig_color = colors[orig]
            move_1_fwrd = orig+self.pawn_moves[orig_color][0]
            move_2_fwrd = orig+self.pawn_moves[orig_color][1]
            move_l_cptr = orig+self.pawn_captures[orig_color][0]
            move_r_cptr = orig+self.pawn_captures[orig_color][1]

            
            if pieces[move_1_fwrd] < 0: # check free space
                moves.add(move_1_fwrd)
            if self.first_rows[orig_color][0] <= orig <= self.first_rows[orig_color][1]: # case 2 moves allowed from 1st row
                if pieces[move_2_fwrd] < 0:
                    moves.add(move_2_fwrd)
            
            # check captures with board boundaries
            if self.mailbox[self.mailbox64[orig]+self.pawn_captures64[orig_color][0]] > -1:
                if colors[move_l_cptr]  == get_opponent_color(orig_color):
                    moves.add(move_l_cptr)
            if self.mailbox[self.mailbox64[orig]+self.pawn_captures64[orig_color][0]] > -1:
                if colors[move_r_cptr] == get_opponent_color(orig_color):
                    moves.add(move_r_cptr)
        return moves