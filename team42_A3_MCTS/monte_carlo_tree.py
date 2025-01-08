import copy
import itertools
import math
import random

from competitive_sudoku.sudoku import GameState, Move, SudokuBoard
from team42_A3_MCTS.check_legal_moves import (
    get_legal_moves,
    get_row,
    get_column,
    get_block,
)

EXPLORATION_FACTOR = 2


class Node:
    ID_ITER = itertools.count()

    def __init__(self, move: Move | None, game_state: GameState):
        self.id = next(self.ID_ITER)
        self.move = move
        self.game_state = game_state
        self.player1_wins = 0
        self.player2_wins = 0
        self.visit_count = 0
        self.uct_score = math.inf
        self.children = []
        self.parent = None

    def __repr__(self):
        parent = self.parent.id if self.parent is not None else "IS ROOT"
        return (
            f"{self.id}-{self.move} | {parent} | Score:{self.uct_score} | Visits:{self.visit_count} | "
            f"{self.player1_wins}-{self.player2_wins} | Player:{self.game_state.current_player}"
        )

    def add_child(self, child_node):
        child_node.parent = self
        self.children.append(child_node)


class MonteCarloTree:
    def __init__(self, game_state: GameState):
        self.root = Node(None, game_state)

    def traverse(self) -> Node:
        """
        STEP 1: Leaf selection
        Traverse the MCT by exploring the children with the greatest UCT scores.
        Returns the leaf node that this path leads to.
        """
        curr_node = self.root

        while len(curr_node.children) > 0:
            best_score = -math.inf
            best_node = None
            # Shuffle the children to randomize the order in which we visit new children.
            for child in random.sample(curr_node.children, len(curr_node.children)):
                if best_score < child.uct_score:
                    best_score = child.uct_score
                    best_node = child
            curr_node = best_node

        return curr_node

    def expand(self, selected_node: Node) -> Node:
        """
        STEP 2: Leaf expansion
        Expand given node and pick one of its children for simulation.
        Returns given leaf node if it can't be expanded.
        """
        moves = get_legal_moves(selected_node.game_state)

        # Expand selected node with all possible moves.
        for move in moves:
            child = Node(move, _make_move(selected_node.game_state, move))
            selected_node.add_child(child)

        return random.choice(selected_node.children) if moves else selected_node

    def simulate(self, selected_node: Node) -> int:
        """
        STEP 3: Simulation
        Simulate the selected node's game state till a final state by making random moves.
        Return the winner (1 or 2), or 0 for draw.
        """
        current_game_state = selected_node.game_state

        player1_out_of_moves = False
        player2_out_of_moves = False
        while True:
            # Condtion 1: Both players are out of moves; End of game.
            if player1_out_of_moves and player2_out_of_moves:
                score_difference = (
                    current_game_state.scores[0] - current_game_state.scores[1]
                )
                return 1 if score_difference > 0 else 2 if score_difference < 0 else 0
            # Condition 2: The current player is out of moves. Switch to the other player.
            if (current_game_state.current_player == 1 and player1_out_of_moves) or (
                current_game_state.current_player == 2 and player2_out_of_moves
            ):
                current_game_state.current_player = (
                    3 - current_game_state.current_player
                )

            # Generate all legal moves of current player.
            legal_moves = get_legal_moves(current_game_state)
            # If no legal moves exists, mark the player as unable to move and restart the loop.
            if len(legal_moves) == 0:
                if current_game_state.current_player == 1:
                    player1_out_of_moves = True
                else:
                    player2_out_of_moves = True
                continue
            # Play a random legal move
            current_game_state = _make_move(
                current_game_state, random.choice(legal_moves)
            )

    def backpropagate(self, simulated_node: Node, winner: int, player: int):
        """
        STEP 4: Backpropagation
        Backpropagate by visiting ancestors of the simulated node.
        On each step update variables and scores.
        """
        current_node = simulated_node

        while current_node is not None:
            current_node.visit_count += 1
            if winner == 1:
                current_node.player1_wins += 1
            elif winner == 2:
                current_node.player2_wins += 1
            elif winner == 0:  # Ties add 0.5 wins to both players
                current_node.player1_wins += 0.5
                current_node.player2_wins += 0.5
            else:
                pass
            current_node.uct_score = _calculate_score(current_node, player)
            current_node = current_node.parent


def _calculate_score(node: Node, player: int) -> float:
    """Calculate the UCT score of a given Node."""
    # Ignore calls on root.
    if node.parent is None:
        return 0

    modifier = -1 if node.game_state.current_player == 1 else 1
    q = modifier * node.player1_wins if player == 1 else modifier * node.player2_wins

    n = node.visit_count
    if n == 0:
        return math.inf

    ln_n = math.log(node.parent.visit_count)
    return (q / n) + EXPLORATION_FACTOR * math.sqrt(ln_n / n)


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


def _remove_duplicates(moves: list[Move]) -> list[Move]:
    """If there are multiple values for a square, pick one randomly."""
    moves_dict = {}  # square -> [values]
    for move in moves:
        if move.square not in moves_dict:
            moves_dict[move.square] = [move.value]
        else:
            moves_dict[move.square].append(move.value)

    pruned_moves = []
    for square, values in moves_dict.items():
        pruned_moves.append(Move(square, random.choice(values)))
    return pruned_moves
