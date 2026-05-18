import random
import numpy as np
import torch
from model.board import encode_board, move_to_index, CheckersNet
from model.rules import legal_moves, is_game_over, get_winner, material_score

MAX_MOVES = 300

class RandomAgent:
    def select_move(self, state, moves):
        return random.choice(moves)

class NeuralAgent:
    def __init__(self, net, temperature=1.0):
        self.net = net
        self.temperature = temperature

    def select_move(self, state, moves):
        if not moves:
            return None

        enc = encode_board(state)
        x = torch.tensor(enc).unsqueeze(0)
        self.net.eval()
        with torch.no_grad():
            _, log_probs = self.net(x)
        log_probs = log_probs.squeeze(0).numpy()

        scores = np.array([log_probs[move_to_index(move)] for move in moves], dtype=np.float64)

        if self.temperature == 0:
            return moves[int(np.argmax(scores))]

        scores -= scores.max()
        probs = np.exp(scores / self.temperature)
        probs /= probs.sum()
        return moves[np.random.choice(len(moves), p=probs)]


def run_self_play(net, num_games=50, temperature=1.0, material_weight=0.3):
    """
    Joue num_games parties de self-play.

    Le résultat cible pour chaque position est un mélange :
        result = (1 - material_weight) * game_result
               +      material_weight  * material_score normalisé

    Ainsi le réseau apprend dès le début qu'avoir plus de pièces est bon,
    sans attendre uniquement le résultat final de la partie.

    material_weight=0.0 -> apprentissage pur résultat (comme avant)
    material_weight=1.0 -> apprentissage pur matériel (heuristique seule)
    material_weight=0.3 -> équilibre recommandé
    """
    from model.board import BoardState
    agent = NeuralAgent(net, temperature=temperature)
    samples = []

    # Score matériel max possible : 20 pions x 1 pt = 20 (normalisé sur [-1, 1])
    MAT_NORM = 20.0

    for _ in range(num_games):
        state = BoardState()
        game_samples = []  # (encoded_board, move_index, player, material_at_position)
        n_moves = 0

        while not is_game_over(state) and n_moves < MAX_MOVES:
            moves = legal_moves(state)
            move = agent.select_move(state, moves)

            enc = encode_board(state)
            idx = move_to_index(move)
            mat = material_score(state) / MAT_NORM   # dans [-1, 1]

            game_samples.append((enc, idx, state.current_player, mat))
            state.apply_move(move)
            n_moves += 1

        winner = get_winner(state)

        for (enc, idx, player, mat) in game_samples:
            # Résultat du point de vue du joueur qui était à ce coup
            if winner == 0:
                game_result = 0.0
            else:
                game_result = 1.0 if winner == player else -1.0

            # Score matériel du point de vue du joueur courant
            mat_from_player = mat if player == 1 else -mat

            result = (1 - material_weight) * game_result + material_weight * mat_from_player
            samples.append((enc, idx, result))

    return samples
