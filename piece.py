from misc import *

class Piece:
    def __init__(self, color="w", type = 1) -> None:
        if color not in player_colors:
            raise ValueError("Wrong piece color entered")
        self._color = color
        self._draw_color = "#000000" if color == "w" else "#FFFFFF"
        self._type = type