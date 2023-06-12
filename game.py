import pygame
from misc import * 
from board import Board
from movegen import MoveGenerator

# pygame setup
pygame.init()
display = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()
running = True
GameBoard = Board(square_dim=64)
MoveGen = MoveGenerator(GameBoard)
(mouse_piece, orig) = None, None

while running:
    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            (mouse_piece, orig) = GameBoard.get_piece_from_mouse(mouse_pos)
            if mouse_piece != None and orig != None:
                allowed_moves = MoveGen.allowed_moves(orig, mouse_piece)
                GameBoard.change_highlights(allowed_moves)
            
        if event.type == pygame.MOUSEBUTTONUP:
           mouse_pos = pygame.mouse.get_pos()
           if mouse_piece != None and orig != None:
               GameBoard.set_piece_at_mouse(mouse_pos, mouse_piece, orig)
               GameBoard.change_highlights([], activate=False, all=True)
               
               
           
    # fill the screen with a color to wipe away anything from last frame
    GameBoard.draw(display)

    # flip() the display to put your work on screen
    pygame.display.update()

    clock.tick(24)  # limits FPS to 60

pygame.quit()