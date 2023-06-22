# test cases for move generation
from view import Board
from model import Model
import pygame
import time
from misc import *
from stockfish import Stockfish
from testcases import perft_testcases


class PerftTest:
    def __init__(self, draw_board=False):
        self.nodes = 0
        self.last_node_cnt = 0
        self.stockfish = Stockfish(
            path=r"C:\Users\kicke\Downloads\stockfish_15.1_win_x64_avx2\stockfish_15.1_win_x64_avx2\stockfish-windows-2022-x86-64-avx2.exe")
        # self.Controls = Controller()
        # self.Controls.run()
        self.GameBoard = Board(square_dim=64)
        self.GameModel = Model(self.GameBoard, sounds=False)
        self.draw_board = draw_board
        self.current_fen = ""
        pygame.init()

    def test_stockfish(self, depth):
        self.stockfish.set_fen_position(self.current_fen)
        self.stockfish.set_depth(depth)
        self.result_stockfish = self.stockfish._perft(depth)

    def test(self):
        for test_idx, test in enumerate(perft_testcases[1:]):
            print(f"Running Testcase {test_idx} | FEN: {test['fen']}")
            self.GameModel.set_fen_string(test["fen"])
            self.draw()
            self.current_fen = test["fen"]
            self.current_depth = test["depth"]
            self.last_node_cnt = 0
            self.res_detailed = {}
            self.test_stockfish(test["depth"])
            nodes = self.perft(test["depth"])
            missing = {}
            for k, v in self.result_stockfish.items():
                if k not in self.res_detailed and k != "total" and "Nodes searched" not in k:
                    missing[k] = v
            print(
                f"RESULT TC{test_idx}: {nodes}/{test['nodes']}/{self.result_stockfish['total']}/ Missing: {missing}")

    def draw(self, delay=0.15):
        if self.draw_board:
            time.sleep(delay)
            self.GameModel.draw()
            pygame.display.update()

    def perft(self, depth, play_turn_color_only=True, print_intermediate=True):
        nodes = 0
        # print("\t Perft Depth ", depth)
        if (depth == 0):
            return 1

        dbg_fen = ""

        legal_moves = self.GameModel.generate_legal_moves()
        # self.GameModel.print_board_state()
        if nodes % 10000:
            print("\t\t Nodes:", nodes)
        for orig, all_dest in legal_moves.items():
            if self.GameModel.player_turn != self.GameModel._colors[orig]: #check if move is players turn
                continue
            for dest in all_dest:
                len_last_move = len(self.GameModel._last_moves)
                self.GameModel.move_piece(orig, dest)
                if depth == self.current_depth:
                    dbg_fen = self.GameModel.get_fen_string()
                    pass
                # assert len_last_move + 1 == len(self.GameModel._last_moves)
                self.draw()
                nodes += self.perft(depth - 1)
                self.GameModel.unmove_piece()
                # assert len_last_move == len(self.GameModel._last_moves)
                self.draw()
                if print_intermediate and depth == self.current_depth:
                    if type(dest) == tuple:
                        dest_idx = dest[0]
                        dest_promo = str(move_desc[dest[1]])[-1]
                    else:
                        dest_idx = dest
                        dest_promo = ""
                    o = self.GameModel.board2alphanum(orig)
                    d = self.GameModel.board2alphanum(dest_idx)
                    comb_move_str = str(o)+str(d)+dest_promo
                    self.res_detailed[comb_move_str] = nodes-self.last_node_cnt
                    res_nodes = nodes-self.last_node_cnt
                    res_expected = self.result_stockfish[comb_move_str]
                    dbg_fen = "" if res_nodes == res_expected else dbg_fen

                    print(
                        f"\t {comb_move_str}: {res_nodes} / {res_expected} -> DBG FEN: {dbg_fen}")
                    self.last_node_cnt = nodes
        return nodes


MoveGenTests = PerftTest()
MoveGenTests.test()
