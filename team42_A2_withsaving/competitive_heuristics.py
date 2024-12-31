### Flow: use get_legal_moves to get a list of moves, then filter it here ###
from competitive_sudoku.sudoku import GameState, Move
from competitive_sudoku.sudokuai import SudokuAI

def wall_heuristic(sudokuai: SudokuAI, moves: list[Move], game_state: GameState) -> list[Move]:
    '''
    Filters a list of legal moves based on a heuristic that attempts to "cut off" the opponent.
    Currently this is implemented by first making a vertical line from the middle column,
    and then making a horizontal wall midway up the board.
    '''
    board_middle = game_state.board.N // 2
    filtered_moves = []

    # Variables to save/load
    save_data = sudokuai.load()
    if(save_data is None):
        save_data = {'curr_phase': 1, 'height': 0, 'broke_through_left': False, 'broke_through_right': False}
    # curr_phase keeps track of the current phase of the strategy. 1 = phase a, 2 = phase b/c, 3 = phase d, 4 = basic minimax
    
    ##### PLAYER 1 #####
    if(game_state.current_player == 1):
        # Get the row number of the row closest to the middle where our player occupies a square
        occupied_height = max([square[0] for square in game_state.occupied_squares1]) if len(game_state.occupied_squares1) > 0 else 0
        
        ### PHASE A ###
        # We must first work our way towards the middle of the board; this is most efficiently done with a vertical line.
        if(save_data['curr_phase'] == 1):
            # Therefore, allow only moves that play in the middle column
            filtered_moves = [move for move in moves if move.square[1] == board_middle]
            # Move on to next phase if no more moves can be played in the middle column or the desired height (middle row) is reached
            if(occupied_height > board_middle or len(filtered_moves) == 0):
                save_data['height'] = min(occupied_height, board_middle)
                save_data['curr_phase'] = 2

        ### PHASE B & C ###
        # Build out  t h e   w a l l
        if(save_data['curr_phase'] == 2):
            # We allow only moves that play in this "middlemost" row
            middle_moves = [move for move in moves if move.square[0] == save_data['height']]
            # We also check if the opponent has already broken through on one or both sides of the middle column
            # Note: with save/load, we only need to check if the *last* move played by the opponent broke through
            last_square = game_state.moves[-1].square
            save_data['broke_through_left'] = save_data['broke_through_left'] or (last_square[0] <= save_data['height'] and last_square[1] < board_middle)
            save_data['broke_through_right'] = save_data['broke_through_right'] or (last_square[0] <= save_data['height'] and last_square[1] > board_middle)

            # If the opponent has broken through on both sides, resort to basic minimax
            if(save_data['broke_through_left'] and save_data['broke_through_right']):
                filtered_moves = moves
                save_data['curr_phase'] = 4
            # If the opponent has broken through on one side, but not the other, build on the other side.
            elif(save_data['broke_through_left']):
                filtered_moves = [move for move in middle_moves if move.square[1] > board_middle]
            elif(save_data['broke_through_right']):
                filtered_moves = [move for move in middle_moves if move.square[1] < board_middle]
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
                            save_data['curr_phase'] = 3
                # Likewise, if we already started building to the right, continue that way
                elif(any(square[1] > board_middle for square in game_state.occupied_squares1)):
                    filtered_moves = [move for move in middle_moves if move.square[1] > board_middle]
                    # If we are already done on the right, go left instead
                    if(len(filtered_moves) == 0):
                        filtered_moves = [move for move in middle_moves if move.square[1] < board_middle]
                        # If we also have nothing to do on the left, move on to phase D
                        if(len(filtered_moves) == 0):
                            save_data['curr_phase'] = 3
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

        ### PHASE D ###
        # At this point, on both sides of the board, we've either completed our wall there or the enemy broke through
        # In this case, allow only moves that *don't* play in captured regions, to deny the enemy as many moves as possible.
        if(save_data['curr_phase'] == 3):
            if(not save_data['broke_through_left'] and not save_data['broke_through_right']):
                filtered_moves = [move for move in moves if move.square[0] > save_data['height']]
            elif(not save_data['broke_through_left']):
                filtered_moves = [move for move in moves if move.square[0] > save_data['height'] or move.square[1] > board_middle]
            elif(not save_data['broke_through_right']):
                filtered_moves = [move for move in moves if move.square[0] > save_data['height'] or move.square[1] < board_middle]
            else:
                filtered_moves = moves

    ##### PLAYER 2 #####
    # If we're player two, the process is similar, except all height comparisons are reversed
    else:
        # Get the row number of the row closest to the middle where our player occupies a square
        occupied_height = min([square[0] for square in game_state.occupied_squares2]) if len(game_state.occupied_squares2) > 0 else game_state.board.N
        
        ### PHASE A ###
        # We must first work our way towards the middle of the board; this is most efficiently done with a vertical line.
        if(occupied_height > board_middle):
            # Therefore, allow only moves that play in the middle column
            filtered_moves = [move for move in moves if move.square[1] == board_middle]

        ### PHASE B & C ###
        # If no more moves can be played in the middle column, or the desired height (middle row) is reached, 
        # switch to building   t h e   w a l l
        if(occupied_height <= board_middle or len(filtered_moves) == 0):
            # We allow only moves that play in this "middlemost" row
            save_data['height'] = max(occupied_height, board_middle)
            middle_moves = [move for move in moves if move.square[0] == save_data['height']]
            # We also check if the opponent has already broken through on one or both sides of the middle column
            save_data['broke_through_left'] = any((square[0] >= save_data['height'] and square[1] < board_middle) for square in game_state.occupied_squares1)
            save_data['broke_through_right'] = any((square[0] >= save_data['height'] and square[1] > board_middle) for square in game_state.occupied_squares1)

            # If the opponent has broken through on both sides, resort to basic minimax
            if(save_data['broke_through_left'] and save_data['broke_through_right']):
                filtered_moves = moves
            # If the opponent has broken through on one side, but not the other, build on the other side.
            elif(save_data['broke_through_left']):
                filtered_moves = [move for move in middle_moves if move.square[1] > board_middle]
            elif(save_data['broke_through_right']):
                filtered_moves = [move for move in middle_moves if move.square[1] < board_middle]
            # If the opponent has broken through on neither side, determine which side to prioritize
            else:
                # If we already started building to the left, continue the wall there
                if(any(square[1] < board_middle for square in game_state.occupied_squares2)):
                    filtered_moves = [move for move in middle_moves if move.square[1] < board_middle]
                    # If we are already done on the left, go right instead
                    if(len(filtered_moves) == 0):
                        filtered_moves = [move for move in middle_moves if move.square[1] > board_middle]
                        # (^ Will be [] if we are also done on the right, in which case we move on to phase D)
                # Likewise, if we already started building to the right, continue that way
                elif(any(square[1] > board_middle for square in game_state.occupied_squares2)):
                    filtered_moves = [move for move in middle_moves if move.square[1] > board_middle]
                    # If we are already done on the right, go left instead
                    if(len(filtered_moves) == 0):
                        filtered_moves = [move for move in middle_moves if move.square[1] < board_middle]
                        # (^ Will be [] if we are also done on the left, in which case we move on to phase D)
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

        ### PHASE D ###
        # At this point, on both sides of the board, we've either completed our wall there or the enemy broke through
        # In this case, allow only moves that *don't* play in captured regions, to deny the enemy as many moves as possible.
        if(len(filtered_moves) == 0):
            if(not save_data['broke_through_left'] and not save_data['broke_through_right']):
                filtered_moves = [move for move in moves if move.square[0] < save_data['height']]
            elif(not save_data['broke_through_left']):
                filtered_moves = [move for move in moves if move.square[0] < save_data['height'] or move.square[1] > board_middle]
            elif(not save_data['broke_through_right']):
                filtered_moves = [move for move in moves if move.square[0] < save_data['height'] or move.square[1] < board_middle]
            else:
                filtered_moves = moves

    ##### RETURN #####
    # As a failsafe, if this filtering leaves us with no moves, then don't filter
    if len(filtered_moves) == 0:
        filtered_moves = moves

    # Save data
    save_data = sudokuai.save(save_data)

    return filtered_moves

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