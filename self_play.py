import numpy as np
import torch
from model.neural_net import ChessNet, encode_board, move_to_index
from model.rules import legal_moves
from controller.game import Game

class NeuralAgent:
    """Agent qui utilise le réseau de neurones pour choisir ses coups."""

    def __init__(self, net, temperature=1.0):
        self.net = net
        self.temperature = temperature  # 0 = greedy, >0 = exploration

    def select_move(self, state, moves):
        if not moves:
            return None

        encoded = encode_board(state)
        tensor = torch.tensor(encoded).unsqueeze(0)

        self.net.eval()
        with torch.no_grad():
            value, log_policy = self.net(tensor)

        log_policy = log_policy.squeeze(0).numpy()

        # Récupérer les probabilités uniquement pour les coups légaux
        move_indices = [move_to_index(m) for m in moves]
        log_probs = log_policy[move_indices]

        if self.temperature == 0:
            # Coup greedy
            best = np.argmax(log_probs)
            return moves[best]
        else:
            # Échantillonnage selon la température
            log_probs = log_probs / self.temperature
            log_probs -= np.max(log_probs)
            probs = np.exp(log_probs)
            probs /= probs.sum()
            idx = np.random.choice(len(moves), p=probs)
            return moves[idx]

class RandomAgent:
    """Agent aléatoire (utile pour les débuts d'entraînement)."""
    def select_move(self, state, moves):
        if not moves:
            return None
        return moves[np.random.randint(len(moves))]

def run_self_play(net, num_games=100, temperature=1.0, verbose=True):
    """
    Lance num_games parties de self-play.
    Retourne une liste de samples : (encoded_state, move_index, result)
    """
    agent = NeuralAgent(net, temperature=temperature)
    all_samples = []

    for game_num in range(num_games):
        game = Game(agent, agent)
        result, history = game.play()

        # Construire les samples avec le résultat propagé
        for state_copy, move, player in history:
            encoded = encode_board(state_copy)
            move_idx = move_to_index(move)
            # result du point de vue du joueur qui a joué
            reward = result * player
            all_samples.append((encoded, move_idx, reward))

        if verbose and (game_num + 1) % 10 == 0:
            print(f"  Parties jouées : {game_num+1}/{num_games} | Dernier résultat : {result:+d} | Samples totaux : {len(all_samples)}")

    return all_samples
