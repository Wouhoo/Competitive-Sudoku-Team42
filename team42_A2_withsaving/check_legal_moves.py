from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove, Square


def get_legal_moves(game_state: GameState) -> list[Move]:
    """
    Checks which moves are legal for the given game state, and return them as a list of Moves.
    """
    N = game_state.board.N
    allowed_squares = GameState.player_squares(game_state)
    # if allowed_squares is None, then every square is an allowed square
    if allowed_squares is None:
        allowed_squares = full_board(game_state)

    legal_moves = []
    taboo_moves = [(move.square, move.value) for move in game_state.taboo_moves]
    # Iterate over all possible moves ((square, value) pairs)
    for square in allowed_squares:
        symbols = set(range(1, N + 1))
        symbols -= get_row(game_state.board, square)
        symbols -= get_column(game_state.board, square)
        symbols -= get_block(game_state.board, square)

        for value in symbols:
            if (square, value) not in taboo_moves:
                legal_moves.append(Move(square, value))

    return legal_moves


def full_board(game_state: GameState) -> list[Square]:
    """Returns all unoccupied squares on the board"""
    empty_board = [
        (i, j) for i in range(game_state.board.N) for j in range(game_state.board.N)
    ]
    occupied_squares = set(game_state.occupied_squares1 + game_state.occupied_squares2)
    return [square for square in empty_board if square not in occupied_squares]


def get_row(board: SudokuBoard, square: Square) -> set[int]:
    """Returns all numbers present in the row that square is in"""
    return set(board.squares[square[0] * board.N : (square[0] + 1) * board.N])


def get_column(board: SudokuBoard, square: Square) -> set[int]:
    """Returns all numbers present in the column that square is in"""
    return set(board.squares[square[1] :: board.N])


def get_block(board: SudokuBoard, square: Square) -> set[int]:
    """Returns all numbers present in the region that square is in"""
    region_row, region_col = (
        square[0] // board.m * board.m,
        square[1] // board.n * board.n,
    )
    return {
        board.get((region_row + i, region_col + j))
        for j in range(board.n)
        for i in range(board.m)
    }


### DEBUG ###
# from competitive_sudoku.sudoku import parse_game_state
# import os
#
# path = os.path.join(os.getcwd(), r"..\\boards\\empty-2x3.txt")
# board_file = open(path, "r")
# test_state = parse_game_state(board_file.read(), playmode="classic")
#
# print(get_row(test_state.board, (2,3)))
