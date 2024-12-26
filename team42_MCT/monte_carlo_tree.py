import copy
import itertools
import math
import random

from competitive_sudoku.sudoku import GameState, Move, SudokuBoard
from team42_MCT.check_legal_moves import get_legal_moves, get_row, get_column, get_block

EXPLORATION_FACTOR = 2

class Node:
    ID_ITER = itertools.count()

    def __init__(self, move: Move, game_state: GameState):
        self.id = next(self.ID_ITER)
        self.move = move
        self.game_state = game_state
        self.player1_wins = 0
        self.player2_wins = 0
        self.visit_count = 0
        self.uct_score = math.inf
        self.children = []
        self.parent = None

    def add_child(self, child_node):
        child_node.parent = self
        self.children.append(child_node)

    def to_string(self):
        return (((str(self.id) + "-" + str(self.move) + "| " +
                (str(self.parent.id) if self.parent is not None else "IS ROOT") +
                "|Score:" + str(self.uct_score)) + "|Visits:" + str(self.visit_count) +
                "|" + str(self.player1_wins) + "-" + str(self.player2_wins)) + "|Player:" +
                str(self.game_state.current_player))

class MonteCarloTree:

    def __init__(self, game_state: GameState):
        self.root = Node(None, game_state)

    #Traverses the MCT by exploring the greatest UCT scores. Returns the leaf node that the path leads.
    def traverse(self) -> Node:
        curr_node = self.root

        while len(curr_node.children) > 0:
            best_score = -math.inf
            best_node = None
            for child in curr_node.children:
                if best_score < child.uct_score:
                    best_score = child.uct_score
                    best_node = child
            curr_node.visit_count += 1
            curr_node = best_node
        curr_node.visit_count += 1
        return curr_node

    #Expands given node and picks one of its children for simulation. Returns given leaf node if can't be expanded.
    def expand(self, selected_node: Node) -> Node:

        moves = get_legal_moves(selected_node.game_state)

        #If we try to expand a terminal state, pass the state for simulation instead.
        first_child = None if len(moves) > 0 else selected_node
        #Expand selected node with all possible moves.
        for move in moves:
            child = Node(move, _make_move(selected_node.game_state, move))
            selected_node.add_child(child)

            #Select first child as a random choice for simulation.
            if first_child is None:
                first_child = child

        return first_child


    #Simulate the selected node's game state till a final state by making random moves. Return the winner (1 or 2)
    # or 0 for draw
    #TODO: Predict winners for slightly faster simulations.
    def simulate(self, selected_node: Node) -> int:
        current_game_state = selected_node.game_state

        player1_out_of_moves = False
        player2_out_of_moves = False
        while True:
            #Condtion 1: Both players are out of moves; End of game.
            if player1_out_of_moves and player2_out_of_moves:
                score_difference = (current_game_state.scores[0] - current_game_state.scores[1])
                return 1 if score_difference > 0 else 2 if score_difference < 0 else 0
            #Condition 2: The current player is out of moves. Switch to the other player.
            if (current_game_state.current_player == 1 and player1_out_of_moves) or (current_game_state.current_player == 2 and player2_out_of_moves):
                current_game_state.current_player = 3 - current_game_state.current_player

            #Generate all legal moves of current player.
            legal_moves = get_legal_moves(current_game_state)
            #If no legal moves exists, mark the player as unable to move and restart the loop.
            if len(legal_moves) == 0:
                if current_game_state.current_player == 1:
                    player1_out_of_moves = True
                else:
                    player2_out_of_moves = True
                continue
            current_game_state = _make_move(current_game_state, random.choice(legal_moves))


    #Back Propagate by visiting parent node of the simulated node. On each step update variables and scores.
    def backpropagate(self, simulated_node: Node, winner: int, player: int):

        current_node = simulated_node
        #Visit count increases during traversal. The simulated node ONLY increases its count on the backprop.
        current_node.visit_count += 1

        while current_node is not None:
            if winner == 1:
                current_node.player1_wins += 1
            elif winner == 2:
                current_node.player2_wins += 1
            #TODO: Figure out UCT score modification on ties. No one wins on ties at the moment.
            else:
                pass
            current_node.uct_score = _calculate_score(current_node, player)
            current_node = current_node.parent


#Calculates the UCT score of given Node
def _calculate_score(node: Node, player: int) -> float:
    #Ignore calls on root.
    if node.parent is None:
        return 0

    q = math.inf
    if player == 1:
        q = -node.player1_wins if node.game_state.current_player == 1 else node.player1_wins
    else:
        q = -node.player2_wins if node.game_state.current_player == 1 else node.player2_wins
    n = node.visit_count
    ln_n = math.log(node.parent.visit_count)

    if n == 0:
        return math.inf

    return (q/n) + EXPLORATION_FACTOR * math.sqrt(ln_n / n)



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