import numpy as np

class TreeSearch:
    def __init__(self, model, depth = 4):
        self.GameModel = model
        self.depth = depth
        pass

    def search(self, search_type="alphabeta"):
        if search_type == "minimax":
            best_score, best_move = self.maxi(self.depth)
        elif search_type == "alphabeta":
            best_score, best_move = self.alphaMax(-float("inf"), float("inf"), self.depth)
        return best_move
    
    def alphaMax(self, alpha, beta, depth):
        max_move = (-1, -1)
        if depth == 0:
            return self.GameModel.eval_board_shannon(), max_move
        legal_moves = self.GameModel.generate_legal_moves(self.GameModel.player_turn, silent=True)
        for orig, all_dest in legal_moves.items():
            for dest in all_dest:
                self.GameModel.move_piece(orig, dest, silent=True)
                score, _ = self.alphaMin(alpha, beta, depth - 1)
                self.GameModel.unmove_piece()
                if score >= beta: # score too good -> enemy will never allow this move, return
                    return beta, max_move
                if score > alpha: # new best score that is not "too" good
                    alpha = score # alpha is max
                    max_move = (orig, dest)
        return alpha, max_move       
    
    def alphaMin(self, alpha, beta, depth):
        min_move = (-1, -1)
        if depth == 0:
            return -self.GameModel.eval_board_shannon(), min_move
        legal_moves = self.GameModel.generate_legal_moves(self.GameModel.player_turn, silent=True)
        for orig, all_dest in legal_moves.items():
            for dest in all_dest:
                self.GameModel.move_piece(orig, dest, silent=True)
                score, _ = self.alphaMax(alpha, beta, depth - 1)
                self.GameModel.unmove_piece()
                if score <= alpha: # score too bad -> do not consider rest as I will not blunder
                    return alpha, min_move
                if score < beta: # new bad score that is not "too" bad but still bad
                    beta = score # beta is min
                    min_move = (orig, dest)
        return beta, min_move 

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
