"""
Self-play avec MCTS : génère des données d'entraînement de haute qualité.
Chaque position est annotée avec la politique MCTS (beaucoup plus riche
qu'un simple coup) et le résultat final de la partie.
"""
import random
import numpy as np
import torch
from model.board import encode_board, move_to_index, BoardState
from model.rules import legal_moves, is_game_over, get_winner, material_score
from model.mcts import MCTS

MAX_MOVES = 300
MAT_NORM  = 20.0


class RandomAgent:
    def select_move(self, state, moves):
        return random.choice(moves)


class NeuralAgent:
    """Agent rapide (sans MCTS) pour les tests et le jeu interactif."""
    def __init__(self, net, temperature=1.0):
        self.net         = net
        self.temperature = temperature

    def select_move(self, state, moves):
        if not moves:
            return None
        enc = encode_board(state)
        x   = torch.tensor(enc).unsqueeze(0)
        self.net.eval()
        with torch.no_grad():
            _, log_probs = self.net(x)
        log_probs = log_probs.squeeze(0).numpy()
        scores = np.array([log_probs[move_to_index(m)] for m in moves], dtype=np.float64)
        if self.temperature == 0:
            return moves[int(np.argmax(scores))]
        scores -= scores.max()
        probs   = np.exp(scores / max(self.temperature, 1e-8))
        probs  /= probs.sum()
        return moves[np.random.choice(len(moves), p=probs)]


class MCTSAgent:
    """Agent fort : utilise le MCTS guidé par le réseau."""
    def __init__(self, net, num_simulations=200, temperature=1.0):
        self.mcts = MCTS(net, num_simulations=num_simulations, temperature=temperature)

    def select_move(self, state, moves=None):
        return self.mcts.select_move(state)


def run_self_play(net, num_games=50, num_simulations=100,
                  temperature=1.0, material_weight=0.2):
    """
    Joue num_games parties par self-play avec MCTS.

    Retourne une liste de (encoded_board, policy_vector, value_target).
    - policy_vector : distribution MCTS sur les 10 000 indices de coups
    - value_target  : mélange résultat + score matériel
    """
    mcts_agent = MCTS(net, num_simulations=num_simulations, temperature=temperature)
    samples    = []

    for game_idx in range(num_games):
        state    = BoardState()
        game_buf = []  # (enc, policy_vec, player, mat)
        n_moves  = 0

        while not is_game_over(state) and n_moves < MAX_MOVES:
            moves, probs = mcts_agent.get_move_probs(state)
            if not moves:
                break

            # Vecteur politique sur 10 000 coups (sparse)
            policy_vec = np.zeros(10000, dtype=np.float32)
            for move, prob in zip(moves, probs):
                policy_vec[move_to_index(move)] = prob

            enc = encode_board(state)
            mat = material_score(state) / MAT_NORM

            game_buf.append((enc, policy_vec, state.current_player, mat))

            # Choisir le coup
            chosen = moves[np.random.choice(len(moves), p=probs)]
            state.apply_move(chosen)
            n_moves += 1

        winner = get_winner(state)

        for (enc, policy_vec, player, mat) in game_buf:
            if winner == 0:
                game_result = 0.0
            else:
                game_result = 1.0 if winner == player else -1.0

            mat_pov = mat if player == 1 else -mat
            value   = (1 - material_weight) * game_result + material_weight * mat_pov
            samples.append((enc, policy_vec, value))

        print(f"    Partie {game_idx + 1}/{num_games} — "
              f"{n_moves} coups — "
              f"gagnant: {'blancs' if winner == 1 else 'noirs' if winner == -1 else 'nulle'}")

    return samples
