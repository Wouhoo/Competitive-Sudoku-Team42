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
from .competitive_heuristics import wall_heuristic
from .sudoku_heuristics import sudoku_heuristics


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

        good_moves = sudoku_heuristics(initial_moves, game_state)
        pruned = [move for move in initial_moves if move not in good_moves]

        current_depth = 1
        # save_data stores information relating to the current phase of the wall strategy between game tree nodes (in memory).
        # This is useful so we don't have to scan the board every time to determine the phase.
        # With file I/O, the phase can also be saved at the end of a turn and loaded at the start of the next turn.
        save_data = self.load() # WITH FILE I/O
        #save_data = None         # WITHOUT FILE I/O
        our_player = game_state.current_player
        while True:
            best_move, save_data = _find_best_move(game_state, save_data, our_player, current_depth, pruned)
            self.propose_move(best_move)
            print(save_data)  # TEST
            self.save(save_data) # WITH FILE I/O
            current_depth += 1


def _find_best_move(game_state: GameState, save_data: dict, our_player: int, depth: int, pruned, ) -> tuple[Move, dict]:
    """Find move using minimax for a given depth.

    Args:
          game_state: state of the game to find a move for.
          depth: depth of the search tree to explore (> 0).

    Returns:
          The move with the highest score, or a random move if all moves are equally good.
    """
    initial_moves, save_data = wall_heuristic(get_legal_moves(game_state), game_state, save_data)
    good_moves = [move for move in initial_moves if move not in pruned]

    is_maximizing = game_state.current_player == 1
    scores = {}
    for i, move in enumerate(good_moves):
        new_state = _make_move(game_state, move)
        score, save_data = _minimax_alphabeta(
            new_state, save_data, our_player, depth=depth - 1, is_maximizing=not is_maximizing, pruned=pruned
        )
        scores[i] = (score, save_data)

    # Sort indices for good_moves by score in decreasing order
    ranked_move_idxs = sorted(scores, key=scores.get, reverse=True)
    best_score = (
        scores[ranked_move_idxs[0]][0] if is_maximizing else scores[ranked_move_idxs[-1]][0]
    )
    best_moves = [(move_idx, save_data) for move_idx, score in scores.items() if score[0] == best_score]
    chosen_move = random.choice(best_moves)
    return good_moves[chosen_move[0]], chosen_move[1]


def _minimax_alphabeta(
    game_state: GameState,
    save_data: dict,
    our_player: int,
    depth: int,
    alpha: float = -math.inf,
    beta: float = math.inf,
    is_maximizing: bool = True,
    pruned=(),
) -> tuple[float, dict]:
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
    if depth == 0:
        return evaluate_state(game_state), save_data

    # Important: for the save/load version of the wall_heuristic, *only our player* must call the wall heuristic function.
    # For the other player, we will consider all legal moves, filtered by the sudoku heuristics.
    if(game_state.current_player == our_player):
        #print("Pre: ", save_data) # TEST
        initial_moves, save_data = wall_heuristic(get_legal_moves(game_state), game_state, save_data)
        #print("Post: ", save_data) # TEST
    else:
        initial_moves = get_legal_moves(game_state)
    good_moves = [move for move in initial_moves if move not in pruned]
    good_moves = sudoku_heuristics(good_moves, game_state)
    pruned = [move for move in initial_moves if move not in good_moves]

    if len(good_moves) == 0:
        return evaluate_state(game_state), save_data

    if is_maximizing:
        value = -math.inf
        for move in good_moves:
            new_state = _make_move(game_state, move)
            new_value, save_data = _minimax_alphabeta(new_state, save_data, our_player, depth - 1, alpha, beta, not is_maximizing, pruned)
            value = max(value, new_value)
            alpha = max(alpha, value)
            if value >= beta:
                break
        return value, save_data
    else:
        value = math.inf
        for move in good_moves:
            new_state = _make_move(game_state, move)
            new_value, save_data = _minimax_alphabeta(new_state, save_data, our_player, depth - 1, alpha, beta, not is_maximizing, pruned)
            value = min(value, new_value)
            beta = min(beta, value)
            if value <= alpha:
                break
        return value, save_data


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
