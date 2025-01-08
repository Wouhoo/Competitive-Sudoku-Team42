import copy
import random

from competitive_sudoku.sudoku import GameState, Move
from team42_A3_MCTS.check_legal_moves import get_legal_moves
from team42_A3_MCTS.evaluation import evaluate_state
from team42_A3_MCTS.monte_carlo_tree import (
    MonteCarloTree,
    Node,
    _remove_duplicates,
    _make_move,
    _move_score
)
from team42_A3_MCTS.sudoku_heuristics import sudoku_heuristics


class MCTSimplified(MonteCarloTree):
    def expand(self, selected_node: Node) -> Node:
        """
        STEP 2: Leaf expansion
        Expand given node and pick one of its children for simulation.
        Returns given leaf node if it can't be expanded.

        Args:
            selected_node: Node to expand from.

        Returns:
            One of the new children of the selected node, or selected_node if it cannot be expanded.
        """
        moves = get_legal_moves(selected_node.game_state)
        # Sudoku heuristic is only useful in the expansion from the root since we do not check values afterward.
        if selected_node == self.root:
            moves = sudoku_heuristics(moves, selected_node.game_state)
        # Select only one value per available square, since we do not simulate values.
        moves = _remove_duplicates(moves)

        # Expand only a few promising moves to keep the branching factor low.
        move_tuples = self._get_promising_moves(selected_node.game_state, moves, count=3)
        for move, next_state, _ in move_tuples:
            child = Node(move, next_state)
            selected_node.add_child(child)

        # Children are ordered by score, so we pick the most promising one first.
        return selected_node.children[0] if selected_node.children else selected_node

    def _get_promising_moves(self, game_state: GameState, moves: list[Move], count=3) -> list[tuple[Move, GameState, float]]:
        """Select the 'count' most promising moves from the given list of moves.
        Returns a tuple of the selected moves, their next game state and the evaluation score.
        """
        move_tuples = []  # [(move, new_state, score),]
        for move in moves:
            new_state = _make_move(game_state, move)
            score = evaluate_state(new_state)
            move_tuples.append((move, new_state, score))

        # Expand only the 3 most promising moves to keep the branching factor low.
        player = game_state.current_player
        move_tuples.sort(key=lambda x: x[2], reverse=player == 1)
        return move_tuples[:count]


    def simulate(self, selected_node: Node, search_depth=1) -> int:
        """Simulate a game of random moves that only look at squares, not their values.

        Args:
            selected_node: Node used as a starting point for simulation.
            search_depth: The fraction of game moves to simulate, where 0.6 would represent 60% of a full game.
                If a game is not finished, the evaluation function determines the winner.

        Returns:
            0, 1 or 2 corresponding to a draw, p1 wins and p2 wins respectively.
        """
        game_state = copy.deepcopy(selected_node.game_state)

        n_moves = min(game_state.board.squares.count(game_state.board.empty), round(search_depth * game_state.board.N ** 2))
        while n_moves > 0:
            legal_squares = game_state.player_squares()
            if not legal_squares:
                game_state.current_player = 3 - game_state.current_player
                continue
            else:
                game_state = _simplified_make_move(game_state, random.choice(legal_squares))

            n_moves -= 1

        if n_moves > 0:
            state_score = evaluate_state(game_state)
        else:
            state_score = game_state.scores[0] - game_state.scores[1]

        if state_score > 0:
            return 1
        elif state_score < 0:
            return 2
        else:
            return 0


def _simplified_make_move(game_state: GameState, square: tuple[int, int]) -> GameState:
    """Return a game state that happens after the given move was performed.
    In this simplified version we ignore the value of each square entirely.

    Args:
        game_state: State of the game before the move.
        square: The square that is played on, this move is assumed to be valid.

    Returns:
        The next state that follows from performing the given move. Dummy values
        are used to mark a move, these are only guaranteed to be unequal to the empty value.
    """
    DUMMY_VALUE = 42  # Used as a placeholder, given that we do not care about values.
    assert DUMMY_VALUE != game_state.board.empty

    game_state.board.put(square, DUMMY_VALUE)

    move_score = _move_score(game_state.board, square)
    game_state.scores[game_state.current_player - 1] += move_score

    if game_state.current_player == 1:
        game_state.occupied_squares1 += [square]
    else:
        game_state.occupied_squares2 += [square]

    game_state.current_player = 3 - game_state.current_player
    return game_state
