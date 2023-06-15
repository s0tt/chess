# write class for chess board with GUI
import pygame
from misc import *
import numpy as np
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

class Board:
    def __init__(self, board_dim=8, screen_dim=(1280, 720), square_dim=8) -> None:
        self.mixer = pygame.mixer.init()
        self.display = pygame.display.set_mode((1280, 720))
        self.display.fill("#bdbdb3")
        self._board_dim = board_dim
        self._screen_dim = screen_dim
        self._square_dim = square_dim
        # self._surface = pygame.Surface(screen_dim)

        self._highlights = np.array([0, 0, 0, 0, 0, 0, 0, 0,
                                     0, 0, 0, 0, 0, 0, 0, 0,
                                     0, 0, 0, 0, 0, 0, 0, 0,
                                     0, 0, 0, 0, 0, 0, 0, 0,
                                     0, 0, 0, 0, 0, 0, 0, 0,
                                     0, 0, 0, 0, 0, 0, 0, 0,
                                     0, 0, 0, 0, 0, 0, 0, 0,
                                     0, 0, 0, 0, 0, 0, 0, 0])
        self._last_move_indices = set()

        self._image_paths = {
            0: r"/mat/pieces/white",
            1: r"/mat/pieces/black"
        }

        self._audio_paths = {
            "check": r"/mat/sounds/move-check.mp3",
            "capture": r"/mat/sounds/capture.mp3",
            "castle": r"/mat/sounds/castle.mp3",
            "move": r"/mat/sounds/move-self.mp3",
            "promote": r"/mat/sounds/promote.mp3",
            "checkmate": r"/mat/sounds/checkmate.mp3",
        }

        self._rects = []

    def draw(self, pieces, colors, attacks):
        self.draw_board(self.display, attacks=attacks)
        self.draw_numbers(self.display)
        self.draw_pieces(self.display, pieces, colors)

    def piece_to_image(self, piece_num, color):
        if 0 < piece_num < len(piece_types)+1:
            if color >= 0:
                img_path = os.path.join(ROOT_DIR, *self._image_paths[color].split("/"), str(piece_num)+".png")
                img = pygame.image.load(img_path)
                return img
            
    def play_sound(self, event_type):
        if event_type in self._audio_paths:
            sound_path = os.path.join(ROOT_DIR, *self._audio_paths[event_type].split("/"))
            sound = pygame.mixer.Sound(sound_path)
            sound.play()
        else:
            raise ValueError("Wrong sound type in play_sound")

    
    def draw_turn_indicator(self, color):
        img =  pygame.font.SysFont(None, 24).render(str("Move indicator:"), True, "#000000")
        rectangle = pygame.Rect(
                    self._square_dim, self._board_dim+1 , (self._square_dim*2), (self._square_dim//2))
        pygame.draw.rect(self.display, player_colors[col_int_to_str[color]], rectangle,0)  # fill rectangle
        self.display.blit(img, (self._square_dim, self._board_dim+1 ))

    def draw_pieces(self, display, pieces, colors):
        for pos in range(self._board_dim**2):
            piece_num = pieces[pos]
            if piece_num > 0:
                img = self.piece_to_image(piece_num, colors[pos])
                if img:
                    display.blit(img, ((pos % self._board_dim) *
                                       self._square_dim, (pos//self._board_dim) *
                                       self._square_dim))

    def draw_numbers(self, display):
        for pos in range(self._board_dim**2):
            img =  pygame.font.SysFont(None, 24).render(str(pos), True, "#000000")
            if img:
                display.blit(img, ((pos % self._board_dim) *
                                    self._square_dim, (pos//self._board_dim) *
                                    self._square_dim))

    def draw_board(self, display, draw_highlights=True, draw_last_move=True, attacks=[]):
        for row in range(self._board_dim):
            for col in range(self._board_dim):
                board_idx = grid2continous(row, col)
                color = player_colors["w"] if (
                    row*self._board_dim+col+row % 2) % 2 == 0 else player_colors["b"]
                if len(attacks) > 0 and attacks[board_idx] > 0:
                    color = attack_color
                if draw_last_move and board_idx in self._last_move_indices:
                    color = last_move_color
                if draw_highlights and self._highlights[board_idx]:
                    # increase R of RGB value for highlights
                    color = highlight_color
                w, h = self._screen_dim
                rectangle = pygame.Rect(
                    col*self._square_dim, row*self._square_dim, (self._square_dim), (self._square_dim))
                # print(f"{color}{row}{col}{rectangle}")
                pygame.draw.rect(display, color, rectangle,
                                 0)  # fill rectangle
                self._rects.append(rectangle)

    def get_rects(self):
        return self._rects
    
    def set_last_move(self, indices : set):
        self._last_move_indices = indices

    def change_highlights(self, indices : set, activate=True, all=False):
        if not all:
            if indices == None:
                return
            self._highlights[list(indices)] = 1 if activate else 0
        else:
            for i in range(self._board_dim**2):
                self._highlights[i] = 1 if activate else 0

    def square_from_mouse(self, mouse_pos, dim1=True):
        row = mouse_pos[1]//self._square_dim
        col = mouse_pos[0]//self._square_dim
        if (self._board_dim <= row) or (self._board_dim <= col):
            return None
        if dim1:
            return row*self._board_dim + col
        else:
            return row, col


