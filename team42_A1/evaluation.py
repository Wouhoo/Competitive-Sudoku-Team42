from competitive_sudoku.sudoku import GameState

def evaluate_state(game_state: GameState) -> float:
    return game_state.scores[0] - game_state.scores[1]
