import pygame
from misc import * 
from view import Board
from model import Model
from search import MiniMax
import numpy as np

class Controller:
    """Controller according to MVC pattern. Handles user input and interaction.
    """
    def __init__(self) -> None:
        pygame.init()
        
        self.clock = pygame.time.Clock()
        self.GameBoard = Board(square_dim=64)
        self.GameModel = Model(self.GameBoard)
        self.MiniMaxSearch = MiniMax(self.GameModel)
        self.mouse_piece, self.orig = None, None
        self.allowed_moves = set()
        self.user_color = 0 # np.randint(0, 2)

    def run(self):
        running = True
        while running:
            # poll for events
            # pygame.QUIT event means the user clicked X to close your window
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if self.GameModel.player_turn == self.user_color: # user turn
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()
                        self.GameModel.handle_mouse_down(mouse_pos)
                        
                    if event.type == pygame.MOUSEBUTTONUP:
                        mouse_pos = pygame.mouse.get_pos()
                        self.GameModel.handle_mouse_up(mouse_pos)
                else: # enemy turn automatic via tree search
                    best_move = self.MiniMaxSearch.search()
                    orig, dest = best_move
                    self.GameModel.move_piece_checked(orig, dest)
                    
                    
                
            # fill the screen with a color to wipe away anything from last frame
            self.GameModel.draw()

            # flip() the display to put your work on screen
            pygame.display.update()

            self.clock.tick(24)  # limits FPS to 60

        pygame.quit()

Controls = Controller()
Controls.run()