from competitive_sudoku.sudoku import GameState

def evaluate_state(game_state: GameState) -> float:
    score_val = game_state.scores[0] - game_state.scores[1]
    space_val = _get_space_value(game_state)
    return score_val + space_val

def _get_space_value(game_state: GameState) -> float:
    """Computes an evaluation of the space for each player, between -1 and 1.
    It compares the playable space for each player as a fraction of the total board.
    Where -1 strongly favours p2, 0 is equal and 1 strongly favours p1.
    """
    current_p = game_state.current_player
    game_state.current_player = 1
    p1_space = len(game_state.player_squares())
    game_state.current_player = 2
    p2_space = len(game_state.player_squares())
    game_state.current_player = current_p  # reset game state
    return (p1_space - p2_space) / game_state.board.N
