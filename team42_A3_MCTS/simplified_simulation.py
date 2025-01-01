import copy
import random

from competitive_sudoku.sudoku import GameState, SudokuBoard
from team42_A3_MCTS.check_legal_moves import get_row, get_column, get_block
from team42_A3_MCTS.monte_carlo_tree import MonteCarloTree, Node
from team42_A3_MCTS.evaluation import evaluate_state


class MCTSimplified(MonteCarloTree):
    def simulate(self, selected_node: Node) -> int:
        """Simulate a game of random moves that only look at squares, not their values."""
        # Simulates this fraction of total game moves, where 1 is a full game.
        search_depth = 0.5

        game_state = selected_node.game_state
        frac_empty = game_state.board.squares.count(game_state.board.empty) / len(
            game_state.board.squares
        )
        initial_empty = frac_empty

        while frac_empty <= max(0, initial_empty - search_depth):
            legal_squares = game_state.player_squares()
            if not legal_squares:
                game_state.current_player = 3 - game_state.current_player
                continue
            else:
                game_state = _simplified_make_move(
                    game_state, random.choice(legal_squares)
                )

            frac_empty = game_state.board.squares.count(game_state.board.empty) / len(
                game_state.board.squares
            )

        if frac_empty > 0:
            state_score = evaluate_state(game_state)
        else:
            state_score = game_state.scores[0] - game_state.scores[1]

        if state_score > 0:
            return 1
        elif state_score < 0:
            return 2
        else:
            return 0


def _simplified_make_move(game_state: GameState, square: tuple[int, int]) -> GameState:
    """Create a new game state that happens after the given move was performed.
    In this simplified version we ignore the value of each square entirely.

    Args:
        game_state: State of the game before the move.
        square: The square that is played on, this move is assumed to be valid.

    Returns:
        The next state that follows from performing the given move. Dummy values
        are used to mark a move, these are only guaranteed to be unequal to the empty value.
    """
    DUMMY_VALUE = 42  # Used as a placeholder, given that we do not care about values.
    assert DUMMY_VALUE != game_state.board.empty

    new_state = copy.deepcopy(game_state)
    new_state.board.put(square, DUMMY_VALUE)

    move_score = _move_score(new_state.board, square)
    new_state.scores[new_state.current_player - 1] += move_score

    if new_state.current_player == 1:
        new_state.occupied_squares1 += [square]
    else:
        new_state.occupied_squares2 += [square]

    new_state.current_player = 3 - new_state.current_player
    return new_state


def _move_score(board: SudokuBoard, square: tuple[int, int]) -> int:
    """Compute the score for the most recent move 'square' and a given board."""
    score = [0, 1, 3, 7]
    n_filled = 0
    for get_region in (get_row, get_column, get_block):
        region = get_region(board, square)
        # Region is filled if there are no empty cells.
        is_filled = board.empty not in region
        n_filled += is_filled

    return score[n_filled]
