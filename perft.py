# test cases for move generation
from view import Board
from model import Model
import pygame
import time
from misc import *
from stockfish import Stockfish
from testcases import perft_testcases, perft_manual_test


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
        self.draw_depth_1 = False
        self.current_fen = ""
        pygame.init()

    def test_stockfish(self, fen, depth):
        self.stockfish.set_fen_position(fen)
        self.stockfish.set_depth(depth)
        self.result_stockfish = self.stockfish._perft(depth)

    def test_all(self):
        for test_idx, test in enumerate(perft_manual_test+perft_testcases[0:]):
            self.test(test["fen"], test["depth"], name=str(test_idx), nodes_expected=test["nodes"])

    def test(self, fen, depth, nodes_expected=-1, name="", recurse_down=True):
        print(f"Running Testcase {name} | FEN: {fen} | Depth: {depth}")
        self.GameModel.set_fen_string(fen)
        self.draw(depth=depth)
        self.current_fen = fen
        self.current_depth = depth
        self.res_detailed = {}
        self.result_stockfish = {}
        self.test_stockfish(fen, depth)
        nodes = self.perft(depth, name=name)
        missing = {}
        for k, v in self.result_stockfish.items():
            if k not in self.res_detailed and k != "total" and "Nodes searched" not in k:
                missing[k] = v
        print(
            f"RESULT TC {name}: {nodes}/{nodes_expected}/{self.result_stockfish['total']}/ Missing: {missing}")
        if len(missing) > 0:
            pass

    def draw(self, depth=None, delay=0.5):
        if self.draw_board or (self.draw_depth_1 and depth == 1):
            time.sleep(delay)
            self.GameModel.draw()
            pygame.display.update()

    def perft(self, depth, name = "", play_turn_color_only=True, print_intermediate=True, dbg_down=True):
        nodes = 0
        moves_before_recurse = 0
        # print("\t Perft Depth ", depth)
        if (depth == 0):
            return 1

        dbg_fen = ""
        if "DBG" in str(name):
            self.draw(depth=1) #force draw at 1
            pass

        legal_moves = self.GameModel.generate_legal_moves()

        for orig, all_dest in legal_moves.items():
            if self.GameModel.player_turn != self.GameModel._colors[orig]: #check if move is players turn
                continue
            for dest in all_dest:
                # if orig == 60 and dest == 62: #dbg
                #     pass
                len_last_move = len(self.GameModel._last_moves)
                self.GameModel.move_piece(orig, dest)
                if depth == self.current_depth:
                    dbg_fen = self.GameModel.get_fen_string()
                    moves_before_recurse = nodes
                    pass
                # assert len_last_move + 1 == len(self.GameModel._last_moves)
                self.draw()
                nodes += self.perft(depth - 1, nodes)
                self.GameModel.unmove_piece()
                # assert len_last_move == len(self.GameModel._last_moves)
                self.draw()
                if depth == self.current_depth:
                    if print_intermediate:
                        if type(dest) == tuple:
                            dest_idx = dest[0]
                            dest_promo = str(move_desc[dest[1]])[-1]
                        else:
                            dest_idx = dest
                            dest_promo = ""
                        o = self.GameModel.board2alphanum(orig)
                        d = self.GameModel.board2alphanum(dest_idx)
                        comb_move_str = str(o)+str(d)+dest_promo
                        res_nodes = nodes-moves_before_recurse
                        self.res_detailed[comb_move_str] = res_nodes
                        res_expected = self.result_stockfish[comb_move_str]
                        dbg_print = "" if res_nodes == res_expected else "-> DBG FEN:" + dbg_fen

                        print(
                            f"\t {comb_move_str}: {res_nodes} / {res_expected} {dbg_print}")
                        if dbg_down and res_nodes != res_expected:
                            self.test(dbg_fen, depth-1, name="###DBG DOWN###", nodes_expected=res_expected)
        return nodes


MoveGenTests = PerftTest()
MoveGenTests.test_all()
