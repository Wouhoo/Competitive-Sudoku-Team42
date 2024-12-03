### Flow: use get_legal_moves to get a list of moves, then filter it here ###
from competitive_sudoku.sudoku import GameState, Move

def wall_heuristic(moves: list[Move], game_state: GameState) -> list[Move]:
    '''
    Filters a list of legal moves based on a heuristic that attempts to "cut off" the opponent.
    Currently this is implemented by first making a vertical line from the middle column,
    and then making a horizontal wall midway up the board.
    '''
    board_middle = game_state.board.N // 2
    
    if(game_state.current_player == 1):
        # Get the row number of the row closest to the middle where our player occupies a square
        occupied_height = max([square[0] for square in game_state.occupied_squares1]) if len(game_state.occupied_squares1) > 0 else 0
        
        # We must first work our way towards the middle of the board; this is most efficiently done with a vertical line.
        if(occupied_height < board_middle):
            # Therefore, allow only moves that play in the middle column
            filtered_moves = [move for move in moves if move.square[1] == board_middle]

        # If no more moves can be played in the middle column, or the desired height (middle row) is reached, 
        # switch to building   t h e   w a l l
        if(occupied_height >= board_middle or len(filtered_moves) == 0):
            # Now allow only moves that play in this row, prioritizing moves to the right
            # (We want to finish one half of the wall before starting the other half, so we at least cut off 1/4 of the board)
            height = min(occupied_height, board_middle)
            filtered_moves = [move for move in moves if (move.square[0] == height and move.square[1] > board_middle)]
            if(len(filtered_moves) == 0):
                filtered_moves = [move for move in moves if move.square[0] == height]

        # If we *also* cannot play anymore moves on the middle row, then we've completed the wall (or the enemy broke through)
        # In this case, prioritize playing moves on the enemy's half of the board to rob them of even more turns
        if(len(filtered_moves) == 0):
            filtered_moves = [move for move in moves if move.square[0] > height]

    # If we're player two, the process is similar, except all height comparisons are reversed
    else:
        # Get the row number of the row closest to the middle where our player occupies a square
        occupied_height = min([square[0] for square in game_state.occupied_squares2]) if len(game_state.occupied_squares2) > 0 else game_state.board.N
        
        # We must first work our way towards the middle of the board; this is most efficiently done with a vertical line.
        if(occupied_height > board_middle):
            # Therefore, allow only moves that play in the middle column
            filtered_moves = [move for move in moves if move.square[1] == board_middle]

        # If no more moves can be played in the middle column, or the desired height (middle row) is reached, 
        # switch to building   t h e   w a l l
        if(occupied_height <= board_middle or len(filtered_moves) == 0):
            # Now allow only moves that play in this row, prioritizing moves to the right
            # (We want to finish one half of the wall before starting the other half, so we at least cut off 1/4 of the board)
            height = max(occupied_height, board_middle)
            filtered_moves = [move for move in moves if (move.square[0] == height and move.square[1] > board_middle)]
            if(len(filtered_moves) == 0):
                filtered_moves = [move for move in moves if move.square[0] == height]

        # If we *also* cannot play anymore moves on the middle row, then we've completed the wall (or the enemy broke through)
        # In this case, prioritize playing moves on the enemy's half of the board to rob them of even more turns
        if(len(filtered_moves) == 0):
            filtered_moves = [move for move in moves if move.square[0] < height]

    # Finally, as a failsafe, if this filtering leaves us with no moves, then don't filter
    if len(filtered_moves) == 0:
        filtered_moves = moves

    return filtered_moves

###################
#
# Observations, thoughts & ideas for future upgrades
#
# - Instead of always rushing to the middle through the middle column, we could make this variable;
#   you could also take a column closer to the edge so that you can more easily capture the part between 
#   the vertical line and the edge (though as a trade-off, cutting off the other half will be harder)
# - Instead of always prioritizing building the wall to the right, we could somehow evaluate the game state
#   to see if building left first would be better.
# - Currently the heuristic just assumes that the wall was succesful if no more moves can be played in the middle row.
#   However, we *do* know if the enemy has broken through, because we know if they occupy a square on our side of the board.
#   We should be able to use this somehow; if they have broken through, then instead of playing on their side,
#   try to block them as much as possible on our side (but in a smart way).
#   Not sure exactly how we want to do this though; the easy thing to do would be to just switch back to minimax
#   if you notice the opponent has broken through, but idk how well that would work (will test next time)
# - After finishing the wall, the heuristic is currently set up to play only on the opponent's half of the board.
#   However, this is not necessarily better, since it might allow the opponent to complete regions using our plays; instead, 
#   we might want to be able to "skip turns" by playing in our captured area, so that we can complete the regions instead.
# - I'm noticing in testing that there is a relatively high risk of proposing a taboo move while building out the wall.
#   Maybe the sudoku heuristics can help prevent this?
# - Also in testing, this strategy seems to be more effective and consistent the larger the board is.
#   (by more consistent I mean that it is less likely that the enemy interferes with the wall.
#    Of course, this would be a different story if the enemy used a similar strategy)
# - When running two A2 agents against eachother, player 1 tends to win (they get to claim one more row),
#   *except* if a move of theirs gets declared taboo and they skip a turn; in that case player 2 can break through p1's wall.
# - <Leave your own ideas here>
#
###################