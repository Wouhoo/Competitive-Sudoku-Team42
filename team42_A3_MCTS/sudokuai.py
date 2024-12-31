#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import copy
import math
import random

import competitive_sudoku.sudokuai
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard
from .check_legal_moves import get_legal_moves, get_row, get_column, get_block
from .monte_carlo_tree import MonteCarloTree


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """
    def __init__(self):
        super().__init__()

    def compute_best_move(self, game_state: GameState) -> None:
        initial_moves = get_legal_moves(game_state)
        # Make sure we have an initial valid move, otherwise we lose the game.
        self.propose_move(random.choice(initial_moves))

        our_player_id = game_state.current_player
        MCT = MonteCarloTree(game_state)

        while True:
            best_leaf_node = MCT.traverse()
            selected_node = MCT.expand(best_leaf_node)
            result = MCT.simulate(selected_node)
            MCT.backpropagate(selected_node, result, our_player_id)
            self.propose_move(_get_best_move(MCT, True))
            #print(_get_best_move(MCT, True)) # TEST


def _get_best_move(tree: MonteCarloTree, is_robust: bool = False) -> Move:
    root = tree.root
    bestScore = -math.inf
    bestChild = None
    for child in root.children:
        #print(child.to_string())
        if child.visit_count == 0:
            continue
        score = child.visit_count if is_robust else (child.player1_wins/child.visit_count)
        if score > bestScore:
            bestScore = score
            bestChild = child
    #print("----------------------")
    return bestChild.move


