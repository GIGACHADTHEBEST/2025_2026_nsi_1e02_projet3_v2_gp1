from model.board import BoardState
from model.rules import legal_moves, is_checkmate, is_draw

MAX_MOVES = 300  # Limite pour éviter les parties infinies

class Game:
    def __init__(self, white_agent, black_agent, view=None):
        """
        white_agent, black_agent : objets avec une méthode select_move(state, moves)
        view : optionnel, objet d'affichage
        """
        self.white_agent = white_agent
        self.black_agent = black_agent
        self.view = view

    def play(self):
        """
        Joue une partie complète.
        Retourne (result, history) où result = 1 (blancs), -1 (noirs), 0 (nulle)
        et history = liste de (state_encoded, move, player)
        """
        state = BoardState()
        history = []
        move_count = 0

        while True:
            if self.view:
                self.view.draw(state)

            moves = legal_moves(state)

            if is_checkmate(state):
                result = -state.current_player  # le joueur qui n'a pas le trait gagne
                if self.view:
                    self.view.draw(state)
                    from view.terminal_view import display_result
                    display_result(result)
                return result, history

            if is_draw(state) or move_count >= MAX_MOVES:
                if self.view:
                    from view.terminal_view import display_result
                    display_result(0)
                return 0, history

            agent = self.white_agent if state.current_player == 1 else self.black_agent
            move = agent.select_move(state, moves)

            history.append((state.copy(), move, state.current_player))
            state.apply_move(move)
            move_count += 1

        return 0, history
