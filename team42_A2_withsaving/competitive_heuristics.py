### Flow: use get_legal_moves to get a list of moves, then filter it here ###
from competitive_sudoku.sudoku import GameState, Move
from competitive_sudoku.sudokuai import SudokuAI

def wall_heuristic(moves: list[Move], game_state: GameState, save_data: dict) -> tuple[list[Move], dict]:
    '''
    Filters a list of legal moves based on a heuristic that attempts to "cut off" the opponent.
    Currently this is implemented by first making a vertical line from the middle column,
    and then making a horizontal wall midway up the board.
    '''
    board_middle = game_state.board.N // 2
    filtered_moves = []

    # Read from save data (containing information about the phase of the strategy in the current game state).
    # If no save data is provided, we are in the first turn, so initialize it
    if(save_data is None):
        save_data = {'old_phase': 1, 'new_phase': 1, 'height': 0, 'broke_through_left': False, 'broke_through_right': False}
    
    try:
        # Check if our player's last move was declared taboo.
        # If yes, we are still in the old phase (*before* the last move was proposed); otherwise, we are in the new phase (*after* the last move went through)
        last_move = game_state.moves[-2]
        last_move_was_taboo = last_move in game_state.taboo_moves
    except:
        # In the beginning of the game, we haven't proposed a move yet
        last_move_was_taboo = False
    # old_phase and new_phase keep track of the current phase of the strategy. 1 = phase a, 2 = phase b/c, 3 = phase d, 4 = basic minimax
    old_phase = save_data['old_phase'] if last_move_was_taboo else save_data['new_phase']   
    new_phase = old_phase
    height = save_data['height']              # The middlemost row number reached by the agent
    broke_through_left = save_data['broke_through_left']   
    broke_through_right = save_data['broke_through_right'] 
    
    ##### PLAYER 1 #####
    if(game_state.current_player == 1):        
        ### PHASE A/1: Work towards the middle of the board along the middle column ###
        if(new_phase == 1):
            # Allow only moves that play in the middle column
            filtered_moves = [move for move in moves if move.square[1] == board_middle]
            # Move on to next phase if no more moves can be played in the middle column or the desired height (middle row) is reached
            height = max([square[0] for square in game_state.occupied_squares1]) if len(game_state.occupied_squares1) > 0 else 0
            if(height >= board_middle or len(filtered_moves) == 0):
                new_phase = 2

        ### Check if the opponent's last move has broken through on either side ###
        try:
            last_square = game_state.moves[-1].square
            broke_through_left = broke_through_left or (last_square[0] <= height and last_square[1] < board_middle)
            broke_through_right = broke_through_right or (last_square[0] <= height and last_square[1] > board_middle)
        except:  # To prevent an error on the first move (where there is no last move)
            pass

        ### PHASE B/2: Build out t h e   w a l l ###
        if(new_phase == 2):
            middle_moves = [move for move in moves if move.square[0] == height]
            # If the opponent has broken through on both sides, resort to basic minimax
            if(broke_through_left and broke_through_right):
                filtered_moves = moves
                new_phase = 4
            # If the opponent has broken through on one side, but not the other, build on the other side.
            elif(broke_through_left):
                filtered_moves = [move for move in middle_moves if move.square[1] > board_middle]
                if(len(filtered_moves) == 0):
                    new_phase = 3
            elif(broke_through_right):
                filtered_moves = [move for move in middle_moves if move.square[1] < board_middle]
                if(len(filtered_moves) == 0):
                    new_phase = 3
            # If the opponent has broken through on neither side, determine which side to prioritize
            else:
                # If we already started building to the left, continue the wall there
                if(any(square[1] < board_middle for square in game_state.occupied_squares1)):
                    filtered_moves = [move for move in middle_moves if move.square[1] < board_middle]
                    # If we are already done on the left, go right instead
                    if(len(filtered_moves) == 0):
                        filtered_moves = [move for move in middle_moves if move.square[1] > board_middle]
                        # If we also have nothing to do on the right, move on to phase D
                        if(len(filtered_moves) == 0):
                            new_phase = 3
                # Likewise, if we already started building to the right, continue that way
                elif(any(square[1] > board_middle for square in game_state.occupied_squares1)):
                    filtered_moves = [move for move in middle_moves if move.square[1] > board_middle]
                    # If we are already done on the right, go left instead
                    if(len(filtered_moves) == 0):
                        filtered_moves = [move for move in middle_moves if move.square[1] < board_middle]
                        # If we also have nothing to do on the left, move on to phase D
                        if(len(filtered_moves) == 0):
                            new_phase = 3
                # Otherwise, we have to choose whether to start building the wall to the right or to the left.
                # Prioritize the side where the opponent has the *fewest* occupied squares.
                # (This block will run once at the start of phase (b) and then never again)
                else:
                    opp_squares_left = len([square for square in game_state.occupied_squares2 if square[1] < board_middle])
                    opp_squares_right = len([square for square in game_state.occupied_squares2 if square[1] > board_middle])
                    if(opp_squares_left < opp_squares_right):
                        filtered_moves = [move for move in middle_moves if move.square[1] < board_middle]
                    else:
                        filtered_moves = [move for move in middle_moves if move.square[1] > board_middle]

        ### PHASE 3/D ###
        # At this point, on both sides of the board, we've either completed our wall there or the enemy broke through
        # In this case, allow only moves that *don't* play in captured regions, to deny the enemy as many moves as possible.
        if(new_phase == 3):
            if(not broke_through_left and not broke_through_right):
                filtered_moves = [move for move in moves if move.square[0] > height]
            elif(not broke_through_left):
                filtered_moves = [move for move in moves if move.square[0] > height or move.square[1] > board_middle]
            elif(not broke_through_right):
                filtered_moves = [move for move in moves if move.square[0] > height or move.square[1] < board_middle]
            else:
                new_phase = 4

        ### PHASE 4/END ###
        # At this point the wall strategy has concluded, and we revert back to basic minimax.
        if(new_phase == 4):
            filtered_moves = moves

    ##### PLAYER 2 #####
    # If we're player two, the process is similar, except all height comparisons are reversed
    else:
        ### PHASE A/1: Work towards the middle of the board along the middle column ###
        if(new_phase == 1):
            # Allow only moves that play in the middle column
            filtered_moves = [move for move in moves if move.square[1] == board_middle]
            # Move on to next phase if no more moves can be played in the middle column or the desired height (middle row) is reached
            height = min([square[0] for square in game_state.occupied_squares2]) if len(game_state.occupied_squares2) > 0 else game_state.board.N
            if(height <= board_middle or len(filtered_moves) == 0):
                new_phase = 2

        ### Check if the opponent's last move has broken through on either side ###
        try:
            last_square = game_state.moves[-1].square
            broke_through_left = broke_through_left or (last_square[0] >= height and last_square[1] < board_middle)
            broke_through_right = broke_through_right or (last_square[0] >= height and last_square[1] > board_middle)
        except:  # To prevent an error on the first move (where there is no last move)
            pass

        ### PHASE B/2: Build out t h e   w a l l ###
        if(new_phase == 2):
            middle_moves = [move for move in moves if move.square[0] == height]
            # If the opponent has broken through on both sides, resort to basic minimax
            if(broke_through_left and broke_through_right):
                filtered_moves = moves
                new_phase = 4
            # If the opponent has broken through on one side, but not the other, build on the other side.
            elif(broke_through_left):
                filtered_moves = [move for move in middle_moves if move.square[1] > board_middle]
                if(len(filtered_moves) == 0):
                    new_phase = 3
            elif(broke_through_right):
                filtered_moves = [move for move in middle_moves if move.square[1] < board_middle]
                if(len(filtered_moves) == 0):
                    new_phase = 3
            # If the opponent has broken through on neither side, determine which side to prioritize
            else:
                # If we already started building to the left, continue the wall there
                if(any(square[1] < board_middle for square in game_state.occupied_squares2)):
                    filtered_moves = [move for move in middle_moves if move.square[1] < board_middle]
                    # If we are already done on the left, go right instead
                    if(len(filtered_moves) == 0):
                        filtered_moves = [move for move in middle_moves if move.square[1] > board_middle]
                        # If we also have nothing to do on the right, move on to phase D
                        if(len(filtered_moves) == 0):
                            new_phase = 3
                # Likewise, if we already started building to the right, continue that way
                elif(any(square[1] > board_middle for square in game_state.occupied_squares2)):
                    filtered_moves = [move for move in middle_moves if move.square[1] > board_middle]
                    # If we are already done on the right, go left instead
                    if(len(filtered_moves) == 0):
                        filtered_moves = [move for move in middle_moves if move.square[1] < board_middle]
                        # If we also have nothing to do on the left, move on to phase D
                        if(len(filtered_moves) == 0):
                            new_phase = 3
                # Otherwise, we have to choose whether to start building the wall to the right or to the left.
                # Prioritize the side where the opponent has the *fewest* occupied squares.
                # (This block will run once at the start of phase (b) and then never again)
                else:
                    opp_squares_left = len([square for square in game_state.occupied_squares1 if square[1] < board_middle])
                    opp_squares_right = len([square for square in game_state.occupied_squares1 if square[1] > board_middle])
                    if(opp_squares_left < opp_squares_right):
                        filtered_moves = [move for move in middle_moves if move.square[1] < board_middle]
                    else:
                        filtered_moves = [move for move in middle_moves if move.square[1] > board_middle]

        ### PHASE 3/D ###
        # At this point, on both sides of the board, we've either completed our wall there or the enemy broke through
        # In this case, allow only moves that *don't* play in captured regions, to deny the enemy as many moves as possible.
        if(new_phase == 3):
            if(not broke_through_left and not broke_through_right):
                filtered_moves = [move for move in moves if move.square[0] < height]
            elif(not broke_through_left):
                filtered_moves = [move for move in moves if move.square[0] < height or move.square[1] > board_middle]
            elif(not broke_through_right):
                filtered_moves = [move for move in moves if move.square[0] < height or move.square[1] < board_middle]
            else:
                new_phase = 4

        ### PHASE 4/END ###
        # At this point the wall strategy has concluded, and we revert back to basic minimax.
        if(new_phase == 4):
            filtered_moves = moves

    ##### RETURN #####
    # As a failsafe, if this filtering leaves us with no moves, then don't filter
    if len(filtered_moves) == 0:
        filtered_moves = moves

    # Save save data
    save_data = {'old_phase': old_phase, 'new_phase': new_phase, 'height': height, 'broke_through_left': broke_through_left, 'broke_through_right': broke_through_right}

    return filtered_moves, save_data

###################
#
# Observations, thoughts & ideas for future upgrades
#
# - Wouter: I'm noticing in testing that there is a relatively high risk of proposing a taboo move while building out the wall.
#   Maybe the sudoku heuristics can help prevent this?
# - Wouter: Also in testing, the wall strategy seems to be more effective and consistent the larger the board is.
#   (by more consistent I mean that it is less likely that the enemy interferes with the wall.
#    Of course, this would be a different story if the enemy used a similarly "aggressive" strategy)
# - Wouter: When running two A2 agents against eachother, player 1 tends to win (they get to claim one more row),
#   *except* if a move of theirs gets declared taboo and they skip a turn; in that case player 2 can break through p1's wall.
# - Nick: Instead of completing the wall on one side all the way, we could instead leave the last square open, and only
#   fill it in if it is within reach of the opponent. This can be generalized to all squares on the middle row;
#   if we can "safely" leave one half of the wall alone (because the opponent can't reach any of the squares in x turns),
#   start working on the other side instead. However, this might be a bit too advanced.
# - Wouter: To evaluate whether going right side first or left side first is better, look at the opponent's occupied squares,
#   and build towards the side where they have more/fewer occupied squares first. Going for the side with *more* squares first
#   is risky, since they have a good chance of breaking through on that side, but if you manage to block them off,
#   you'll probably get the other side as well. Going for the side with *fewer* squares first is safe, they probably won't
#   break through on that side and you can secure 1/4 of the board; however, securing the other side is a lot harder
#   (if not impossible) afterwards. So the question is, do we gamble for 1/2 of the board or safely claim 1/4?
#   Personally, since claiming 1/4 is often enough to win the game, I say we play safe. That's how it's currently implemented.
# - Wouter: Instead of always rushing to the middle through the middle column, we could make this variable;
#   you could also take a column closer to the edge so that you can more easily capture the part between 
#   the vertical line and the edge (though as a trade-off, cutting off the other half will be harder)
# - Wouter: After finishing the wall, the heuristic is currently set up to not play on captured areas.
#   However, this is not necessarily better, since it might allow the opponent to complete regions using our plays; instead, 
#   we might want to be able to "skip turns" by playing in our captured area, so that we can complete the regions instead.
#   This can be achieved by "soft-filtering" instead of "hard-filtering"; currently we do not allow the agent to play
#   on captured areas *at all*, but we might want to allow this, just with a lower evaluation value.
# - <Leave your own ideas here>
#
#
# OLD COMMENTS (RESOLVED BY v2.0)
# - Instead of always prioritizing building the wall to the right, we could somehow evaluate the game state
#   to see if building left first would be better.
# - Currently the heuristic just assumes that the wall was succesful if no more moves can be played in the middle row.
#   However, we *do* know if the enemy has broken through, because we know if they occupy a square on our side of the board.
#   We should be able to use this somehow; if they have broken through, then instead of playing on their side,
#   try to block them as much as possible on our side (but in a smart way).
#   Not sure exactly how we want to do this though; the easy thing to do would be to just switch back to minimax
#   if you notice the opponent has broken through, but idk how well that would work (will test next time)
#
###################