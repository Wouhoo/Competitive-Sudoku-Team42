import copy
from functools import lru_cache, reduce
from itertools import combinations

from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, Square
from .check_legal_moves import get_row, get_column, get_block


def sudoku_heuristics(moves: list[Move], game_state: GameState) -> list[Move]:
    """Filter out moves that make the sudoku unsolvable.

    Args:
        moves: list of considered moves.
        game_state: current state of the game.

    Returns:
        A new list of moves such that new_list is a subset of 'moves'.
    """
    moves_dict = {}  # square -> {values}
    for move in moves:
        if move.square not in moves_dict:
            moves_dict[move.square] = {move.value}
        else:
            moves_dict[move.square].add(move.value)

    new_moves = only_squares_rule(moves_dict, game_state.board)
    # hidden_pair and naked_pair did not perform well on the smallest board size.
    if game_state.board.N > 4:
        new_moves = hidden_twin_rule(new_moves, game_state.board, group_size=2)
        new_moves = naked_twin_rule(new_moves, game_state.board, group_size=2)

    # Convert the resulting moves dict back into a list of moves.
    out = []
    for square, values in new_moves.items():
        for value in values:
            out.append(Move(square, value))

    return out


def only_squares_rule(moves: dict, board: SudokuBoard) -> dict:
    """Applies the subgroup exclusion rule from SudokuDragon.

    Args:
        moves: dictionary of suggested moves (square -> set of suggested values).
        board: current board

    Returns:
        An updated set of moves which has needless options removed. Remains the
        same as 'moves' if no options were excluded.
    """

    def apply_rule(squares, values: set[int], board: SudokuBoard) -> set[int]:
        available = set()
        for square in squares:
            if board.get(square) == board.empty:
                available.update(_square_valid_moves(square, board))

        if values - available:
            return values - available
        else:
            return values

    out = copy.deepcopy(moves)
    for square, considered_vals in moves.items():
        values = _square_valid_moves(square, board)
        if len(values) <= 1:
            continue

        groups = [
            _get_row_squares(square[0], board) - {square},
            _get_col_squares(square[1], board) - {square},
            _get_region_squares(square, board) - {square},
        ]
        for group in groups:
            found_vals = apply_rule(group, values, board)
            if len(found_vals) == 1:
                out[square] = considered_vals.intersection(found_vals)
                break

    return out


def hidden_twin_rule(moves: dict, board: SudokuBoard, group_size=2) -> dict:
    """Applies the hidden-twin rule from SudokuDragon.

    Args:
        moves: dictionary of suggested moves (square -> set of suggested values).
        board: current board.
        group_size: size of the group to look for using this method. Default 2 for twins.

    Returns:
        An updated set of moves which has needless options removed. Remains the
        same as 'moves' if no options were excluded.
    """

    def apply_rule(squares, values, board):
        group_moves = [_square_valid_moves(square, board) for square in squares]
        for subset in combinations(values, group_size):
            subset = set(subset)
            if sum([subset.issubset(val) for val in group_moves]) == group_size - 1:
                if (
                    sum([subset.intersection(val) != set() for val in group_moves])
                    == group_size - 1
                ):
                    return subset

        return values

    out = copy.deepcopy(moves)
    for square, considered_vals in moves.items():
        values = _square_valid_moves(square, board)
        if len(values) <= group_size:
            continue

        groups = [
            _get_row_squares(square[0], board) - {square},
            _get_col_squares(square[1], board) - {square},
            _get_region_squares(square, board) - {square},
        ]
        for group in groups:
            group = {square for square in group if board.get(square) == board.empty}
            found_vals = apply_rule(group, values, board)
            if len(found_vals) == group_size:
                out[square] = considered_vals.intersection(found_vals)
                break

    return out


def naked_twin_rule(moves: dict, board: SudokuBoard, group_size=2) -> dict:
    """Applies the hidden-twin rule from SudokuDragon.

    Args:
        moves: dictionary of suggested moves (square -> set of suggested values).
        board: current board.
        group_size: size of the group to look for using this method. Default 2 for twins.

    Returns:
        An updated set of moves which has needless options removed. Remains the
        same as 'moves' if no options were excluded."""

    def apply_rule(squares, values, board):
        group_moves = [_square_valid_moves(square, board) for square in squares]
        available = reduce(lambda x, y: x.union(y), group_moves, set())

        for subset in combinations(available, group_size):
            subset = set(subset)
            # Pairs without any considered moves do not give us information.
            if len(values.intersection(subset)) == 0:
                continue

            if sum([subset == val for val in group_moves]) == group_size:
                return values - subset

        return values

    out = copy.deepcopy(moves)
    for square, values in moves.items():
        if len(values) <= group_size:
            continue

        groups = [
            _get_row_squares(square[0], board) - {square},
            _get_col_squares(square[1], board) - {square},
            _get_region_squares(square, board) - {square},
        ]
        for group in groups:
            group = {square for square in group if board.get(square) == board.empty}
            found_vals = apply_rule(group, values, board)
            if found_vals != out[square]:
                out[square] = found_vals
                break

    return out


@lru_cache
def _square_valid_moves(square: Square, board: SudokuBoard) -> set[int]:
    """Find all numbers that can be played on this square. Assumes the square is empty."""
    valid_numbers = set(range(1, board.N + 1))
    valid_numbers -= get_row(board, square)
    valid_numbers -= get_column(board, square)
    valid_numbers -= get_block(board, square)
    return valid_numbers


def _get_row_squares(row_idx, board) -> set[Square]:
    return {(row_idx, i) for i in range(board.N)}


def _get_col_squares(col_idx, board) -> set[Square]:
    return {(i, col_idx) for i in range(board.N)}


def _get_region_squares(square, board) -> set[Square]:
    x = square[0] // board.n * board.n
    y = square[1] // board.m * board.m
    return {(x + i, y + j) for i in range(board.n) for j in range(board.m)}
