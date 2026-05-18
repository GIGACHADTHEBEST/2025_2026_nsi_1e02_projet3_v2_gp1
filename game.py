from model.rules import legal_moves, is_game_over, get_winner

class Game:
    def __init__(self, agent_white, agent_black):
        self.agents = {1: agent_white, -1: agent_black}

    def run(self, state, max_moves=300, verbose=False):
        from view.terminal_view import display_board, move_to_notation
        n = 0
        while not is_game_over(state) and n < max_moves:
            moves = legal_moves(state)
            agent = self.agents[state.current_player]
            move = agent.select_move(state, moves)
            if verbose:
                display_board(state)
                print(f"  -> {move_to_notation(move)}")
            state.apply_move(move)
            n += 1
        return get_winner(state)
