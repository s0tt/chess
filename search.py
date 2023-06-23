import numpy as np

class MiniMax:
    def __init__(self, model, depth = 4):
        self.GameModel = model
        self.depth = depth
        pass

    def search(self):
        best_score, best_move = self.maxi(self.depth)
        return best_move
    
    def maxi(self, depth):
        if depth == 0:
            return self.GameModel.eval_board_shannon(), (-1, -1)
        max_score = -float("inf")
        max_move = (-1, -1)
        legal_moves = self.GameModel.generate_legal_moves(self.GameModel.player_turn, silent=True)
        for orig, all_dest in legal_moves.items():
            for dest in all_dest:
                self.GameModel.move_piece(orig, dest, silent=True)
                score, _ = self.mini(depth - 1)
                self.GameModel.unmove_piece()
                if score > max_score:
                    max_score = score
                    max_move = (orig, dest)
        return max_score, max_move
    
    def mini(self, depth):
        if depth == 0:
            return -self.GameModel.eval_board_shannon(), (-1, -1)
        min_score = float("inf")
        min_move = (-1, -1)
        legal_moves = self.GameModel.generate_legal_moves(self.GameModel.player_turn)
        for orig, all_dest in legal_moves.items():
            for dest in all_dest:
                self.GameModel.move_piece(orig, dest, silent=True)
                score, _ = self.maxi(depth - 1)
                self.GameModel.unmove_piece()
                if score < min_score:
                    min_score = score
                    min_move = (orig, dest)
        return min_score, min_move
