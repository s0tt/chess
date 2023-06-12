# write class for chess board with GUI
import pygame
from misc import *
import numpy as np
import os


class Board:
    def __init__(self, board_dim=8, screen_dim=(1280, 720), square_dim=8) -> None:
        self._board_dim = board_dim
        self._screen_dim = screen_dim
        self._square_dim = square_dim
        # self._surface = pygame.Surface(screen_dim)

        self._colors = np.array([1, 1, 1, 1, 1, 1, 1, 1,
                                 1, 1, 1, 1, 1, 1, 1, 1,
                                 -1, -1, -1, -1, -1, -1, -1, -1,
                                 -1, -1, -1, -1, -1, -1, -1, -1,
                                 -1, -1, -1, -1, -1, -1, -1, -1,
                                 -1, -1, -1, -1, -1, -1, -1, -1,
                                 0, 0, 0, 0, 0, 0, 0, 0,
                                 0, 0, 0, 0, 0, 0, 0, 0])

        self._highlights = np.array([0, 0, 0, 0, 0, 0, 0, 0,
                                     0, 0, 0, 0, 0, 0, 0, 0,
                                     0, 0, 0, 0, 0, 0, 0, 0,
                                     0, 0, 0, 0, 0, 0, 0, 0,
                                     0, 0, 0, 0, 0, 0, 0, 0,
                                     0, 0, 0, 0, 0, 0, 0, 0,
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
        self._image_paths = {
            0: r"/mat/pieces/white",
            1: r"/mat/pieces/black"
        }
        self._rects = []

    def draw(self, display):
        self.draw_board(display)
        self.draw_pieces(display)

    def piece_to_image(self, piece_num, color):
        if 0 < piece_num < len(piece_types)+1:
            if color >= 0:
                img_path = os.path.join(os.getcwd(
                ), *self._image_paths[color].split("/"), str(piece_num)+".png")
                img = pygame.image.load(img_path)
                return img

    def draw_pieces(self, display):
        for pos in range(self._board_dim**2):
            piece_num = self._pieces[pos]
            if piece_num > 0:
                img = self.piece_to_image(piece_num, self._colors[pos])
                if img:
                    display.blit(img, ((pos % self._board_dim) *
                                       self._square_dim, (pos//self._board_dim) *
                                       self._square_dim))

    def draw_board(self, display, draw_highlights=True):
        for row in range(self._board_dim):
            for col in range(self._board_dim):
                color = player_colors["w"] if (
                    row*self._board_dim+col+row % 2) % 2 == 0 else player_colors["b"]
                if draw_highlights and self._highlights[(row*self._board_dim + col)]:
                    # increase R of RGB value for highlights
                    color = (
                        min(color[0]+highlight_red_offset, 255), *color[1:])
                w, h = self._screen_dim
                rectangle = pygame.Rect(
                    col*self._square_dim, row*self._square_dim, (self._square_dim), (self._square_dim))
                # print(f"{color}{row}{col}{rectangle}")
                pygame.draw.rect(display, color, rectangle,
                                 0)  # fill rectangle
                self._rects.append(rectangle)

    def get_rects(self):
        return self._rects

    def get_piece(self, idx):
        return self._pieces[idx]

    def get_piece_from_mouse(self, mouse_pos):
        board_idx = self.square_from_mouse(mouse_pos)
        piece = self._pieces[board_idx]
        if piece > 0:
            return (piece, board_idx)
        else:
            return (None, None)  # no piece there

    def set_piece_at_mouse(self, mouse_pos, piece, orig):
        board_idx = self.square_from_mouse(mouse_pos)
        if piece:
            if board_idx != orig:
                # set piece type
                self._pieces[board_idx] = piece
                self._pieces[orig] = -1

                # set color
                self._colors[board_idx] = self._colors[orig]
                self._colors[orig] = -1

    def square_from_mouse(self, mouse_pos, dim1=True):
        row = mouse_pos[1]//self._square_dim
        col = mouse_pos[0]//self._square_dim
        if self._board_dim <= row < 0 or self._board_dim <= col < 0:
            return None
        if dim1:
            return row*self._board_dim + col
        else:
            return row, col

    def change_highlights(self, indices, activate=True, all=False):
        if not all:
            if indices == None:
                return
            for idx in indices:
                self._highlights[idx] = 1 if activate else 0
        else:
            for i in range(self._board_dim**2):
                self._highlights[i] = 1 if activate else 0
