### Script for running tests automatically ###
from simulate_game import play_game

### TEST PARAMETERS ###
board = "boards/empty-3x3.txt"
agent1 = "team42_A2"
agent2 = "greedy_player"
calculation_time = 0.1

no_tests = 10   # nr. of tests to run with these settings (make sure this is even so both agents play as player 1 an equal number of times)

# Don't change these unless you have a good reason to
verbose = False
warmup = False
playmode = 'rows'
#######################

agent1_wins = 0
agent2_wins = 0

print('------------------------------')
print('Commencing tests')
print('------------------------------')

for game_no in range(no_tests):
    # Agent 1 will be player 1 in even-numbered games and player 2 in odd-numbered games
    if(game_no % 2 == 0):
        result = play_game(board_file=board, name1=agent1, name2=agent2, calculation_time=calculation_time, verbose=verbose, warmup=warmup, playmode=playmode)
        agent1_wins += result[0]
        agent2_wins += result[1]
    else:
        result = play_game(board_file=board, name1=agent2, name2=agent1, calculation_time=calculation_time, verbose=verbose, warmup=warmup, playmode=playmode)
        agent1_wins += result[1]
        agent2_wins += result[0]

print('------------------------------')
print('Test results')
print('------------------------------')
print('No. of games simulated: {}'.format(no_tests))
print('Computation time: {}'.format(calculation_time))
print('Board file: {}'.format(board))
print('Agent 1: {} won {} games ({}%)'.format(agent1, agent1_wins, (agent1_wins/no_tests)))
print('Agent 2: {} won {} games ({}%)'.format(agent2, agent2_wins, (agent2_wins/no_tests)))
print('------------------------------')