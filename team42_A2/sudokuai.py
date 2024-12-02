#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import copy
import math
import random

import competitive_sudoku.sudokuai
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard
from .check_legal_moves import get_legal_moves, get_row, get_column, get_block
from .evaluation import evaluate_state


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """
    def __init__(self):
        super().__init__()

    def compute_best_move(self, game_state: GameState) -> None:
        legal_moves = get_legal_moves(game_state)
        # Make sure we have an initial valid move, otherwise we lose the game.
        self.propose_move(random.choice(legal_moves))

        current_depth = 1
        while True:
            self.propose_move(_find_best_move(game_state, current_depth))
            current_depth += 1

def _find_best_move(game_state: GameState, depth: int) -> Move:
    """Find move using minimax for a given depth.

    Args:
          game_state: state of the game to find a move for.
          depth: depth of the search tree to explore (> 0).

    Returns:
          The move with the highest score, or a random move if all moves are equally good.
    """
    legal_moves = get_legal_moves(game_state)

    is_maximizing = game_state.current_player == 1
    scores = {}
    for i, move in enumerate(legal_moves):
        new_state = _make_move(game_state, move)
        score = _minimax_alphabeta(new_state, depth=depth - 1, is_maximizing=not is_maximizing)
        scores[i] = score

    # Sort indices for legal_moves by score in decreasing order
    ranked_move_idxs = sorted(scores, key=scores.get, reverse=True)
    best_score = scores[ranked_move_idxs[0]] if is_maximizing else scores[ranked_move_idxs[-1]]
    best_moves = [move_idx for move_idx, score in scores.items() if score == best_score]
    return legal_moves[random.choice(best_moves)]


def _minimax_alphabeta(
        game_state: GameState, depth: int, alpha: float = -math.inf, beta: float = math.inf, is_maximizing: bool = True
) -> float:
    """Implementation of the minimax scoring function with alpa-beta pruning.

    Args:
        game_state: state of the game to score.
        depth: depth of the state tree to evaluate (>= 0).
        alpha: alpha value for alpha-beta pruning, -inf for initial call.
        beta: beta value for alpha-beta pruning, inf for initial call.
        is_maximizing: whether the evaluation is for the maximizing player.

    Returns:
        Score for the given state.
    """
    legal_moves = get_legal_moves(game_state)
    if depth == 0 or len(legal_moves) == 0:
        return evaluate_state(game_state)

    if is_maximizing:
        value = -math.inf
        for move in legal_moves:
            new_state = _make_move(game_state, move)
            value = max(value, _minimax_alphabeta(new_state, depth - 1, alpha, beta, not is_maximizing))
            alpha = max(alpha, value)
            if value >= beta:
                break
        return value
    else:
        value = math.inf
        for move in legal_moves:
            new_state = _make_move(game_state, move)
            value = min(value, _minimax_alphabeta(new_state, depth - 1, alpha, beta, not is_maximizing))
            beta = min(beta, value)
            if value <= alpha:
                break
        return value


def _make_move(game_state: GameState, move: Move) -> GameState:
    """Create a new game state that happens after the given move was performed.
    Taboo moves are not added, the sudoku is assumed to remain solvable after any move.

    Args:
        game_state: State of the game before the move.
        move: The move to make. Move is assumed to be valid.

    Returns:
        The next state that follows from performing the given move.
    """
    new_state = copy.deepcopy(game_state)
    new_state.board.put(move.square, move.value)
    new_state.moves.append(move)

    move_score = _move_score(new_state.board, move.square)
    new_state.scores[new_state.current_player - 1] += move_score

    if new_state.current_player == 1:
        new_state.occupied_squares1 += [move.square]
    else:
        new_state.occupied_squares2 += [move.square]

    new_state.current_player = 3 - new_state.current_player
    return new_state


def _move_score(board: SudokuBoard, square: tuple[int, int]) -> int:
    """Compute the score for the most recent move 'square' and a given board."""
    score = [0, 1, 3, 7]
    n_filled = 0
    for get_region in (get_row, get_column, get_block):
        region = get_region(board, square)
        # Region is filled if there are no empty cells.
        is_filled = 0 not in region
        n_filled += is_filled

    return score[n_filled]
