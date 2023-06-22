# test cases for move generation
from view import Board
from model import Model
import pygame
import time
from misc import *
from stockfish import Stockfish
from testcases import perft_testcases, perft_manual_test


class PerftTest:
    """_summary_
    Class to evaluate chess engine by using external FEN game string and test calculated nodes.
    Divide is possible to recurse down the tree of possible moves.
    """

    def __init__(self, draw_board=True):
        """_summary_

        Args:
            draw_board (bool, optional): Flag to trigger board draw when testing. Defaults to False.
        """
        self.nodes = 0
        self.last_node_cnt = 0
        self.stockfish = Stockfish(
            path=r"C:\Users\kicke\Downloads\stockfish_15.1_win_x64_avx2\stockfish_15.1_win_x64_avx2\stockfish-windows-2022-x86-64-avx2.exe")
        self.GameBoard = Board(square_dim=64)
        self.GameModel = Model(self.GameBoard, sounds=False)
        self.draw_board = draw_board
        self.draw_depth_1 = False
        self.current_fen = ""
        pygame.init()

    def test_stockfish(self, fen: str, depth: int):
        """Calculate available moves via Stockfish engine for comparison.
            Uses python stockfish api: pip install stockfish with custom extension to perft

        Args:
            fen (_type_): FEN game notation string
            depth (_type_): recursion search depth
        """
        self.stockfish.set_fen_position(fen)
        self.stockfish.set_depth(depth)
        self.result_stockfish = self.stockfish._perft(depth)

    def test_all(self):
        for test_idx, test in enumerate(perft_manual_test+perft_testcases[0:]):
            self.test(test["fen"], test["depth"], name=str(
                test_idx), nodes_expected=test["nodes"])

    def test(self, fen: str, depth: int, nodes_expected=-1, name="", recurse_down=True):
        """_summary_

        Args:
            fen (str): _description_
            depth (_type_): _description_
            nodes_expected (int, optional): _description_. Defaults to -1.
            name (str, optional): _description_. Defaults to "".
            recurse_down (bool, optional): _description_. Defaults to True.
        """
        print(f"\nRunning Testcase {name} | FEN: {fen} | Depth: {depth}")
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

        start_col, end_col = "", ""
        if nodes != nodes_expected or len(missing) > 0:
            start_col = bcolors.WARNING
            end_col = bcolors.ENDC
        print(
            f"\t{start_col}RESULT TC {name}: {nodes}/{nodes_expected}/{self.result_stockfish['total']}/ Missing: {missing} {end_col}")
        if len(missing) > 0:
            pass

    def draw(self, depth=None, delay=0.001):
        if self.draw_board or (self.draw_depth_1 and depth == 1):
            time.sleep(delay)
            self.GameModel.draw()
            pygame.display.update()

    def perft(self, depth: int, name="", play_turn_color_only=True, print_intermediate=False, dbg_down=True):
        """Performance testing (perft) function to test engine with challenging cases

        Args:
            depth (int): recursion depth
            name (str, optional): Run name. Defaults to "".
            play_turn_color_only (bool, optional): _description_. Defaults to True.
            print_intermediate (bool, optional): _description_. Defaults to False.
            dbg_down (bool, optional): _description_. Defaults to True.

        Returns:
            _type_: _description_
        """
        nodes = 0
        moves_before_recurse = 0
        # print("\t Perft Depth ", depth)
        if (depth == 0):
            return 1

        dbg_fen = ""
        if "DBG" in str(name):
            self.draw(depth=1)  # force draw at 1
            pass

        legal_moves = self.GameModel.generate_legal_moves()

        for orig, all_dest in legal_moves.items():
            # check if move is players turn
            if self.GameModel.player_turn != self.GameModel._colors[orig]:
                continue
            for dest in all_dest:
                len_last_move = len(self.GameModel._last_moves)
                self.GameModel.move_piece(orig, dest)
                if depth == self.current_depth:
                    dbg_fen = self.GameModel.get_fen_string()
                    moves_before_recurse = nodes
                    pass

                # actual recursive move execution
                self.draw()
                nodes += self.perft(depth - 1, nodes)
                self.GameModel.unmove_piece()

                self.draw()

                # print intermediate division step results
                if depth == self.current_depth:
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

                    if print_intermediate:
                        dbg_print = "" if res_nodes == res_expected else "-> DBG FEN:" + dbg_fen
                        print(
                            f"\t {comb_move_str}: {res_nodes} / {res_expected} {dbg_print}")

                    if dbg_down and res_nodes != res_expected:
                        self.test(dbg_fen, depth-1, name="###DBG DOWN###", nodes_expected=res_expected)
        return nodes


MoveGenTests = PerftTest()
MoveGenTests.test_all()
