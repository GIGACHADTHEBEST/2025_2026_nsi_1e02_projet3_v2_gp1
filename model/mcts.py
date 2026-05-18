"""
Monte Carlo Tree Search (MCTS) — version AlphaZero.

Le MCTS explore l'arbre de jeu en guidant la recherche grâce
au réseau de neurones (politique + valeur). C'est ce composant
qui transforme un réseau moyen en IA très forte.
"""
import math
import numpy as np
import torch
from model.board import encode_board, move_to_index
from model.rules import legal_moves, is_game_over, get_winner

C_PUCT = 1.4          # Constante d'exploration UCB
DIRICHLET_ALPHA = 0.3  # Bruit Dirichlet à la racine (encourage l'exploration)
DIRICHLET_EPS   = 0.25


class MCTSNode:
    __slots__ = ['state', 'parent', 'move', 'children',
                 'W', 'N', 'Q', 'P', 'is_expanded', 'player']

    def __init__(self, state, parent=None, move=None, prior=0.0):
        self.state      = state
        self.parent     = parent
        self.move       = move       # Coup qui a mené ici
        self.children   = []
        self.W          = 0.0        # Somme des valeurs
        self.N          = 0          # Nombre de visites
        self.Q          = 0.0        # Valeur moyenne
        self.P          = prior      # Probabilité a priori (réseau)
        self.is_expanded = False
        self.player     = state.current_player  # Joueur qui JOUE depuis ce nœud

    def ucb_score(self, total_visits):
        """Score UCB1 façon AlphaZero."""
        u = C_PUCT * self.P * math.sqrt(total_visits) / (1 + self.N)
        return self.Q + u

    def backup(self, value):
        """Remonte la valeur dans l'arbre."""
        self.N += 1
        self.W += value
        self.Q = self.W / self.N
        if self.parent:
            # La valeur est du point de vue du joueur qui vient de jouer,
            # donc on inverse pour le parent (qui est l'adversaire)
            self.parent.backup(-value)


class MCTS:
    def __init__(self, net, num_simulations=200, temperature=1.0):
        self.net             = net
        self.num_simulations = num_simulations
        self.temperature     = temperature

    def _evaluate(self, state):
        """Évalue un état avec le réseau."""
        enc = encode_board(state)
        x   = torch.tensor(enc).unsqueeze(0)
        self.net.eval()
        with torch.no_grad():
            value, log_policy = self.net(x)
        value     = value.item()
        log_policy = log_policy.squeeze(0).numpy()
        return value, log_policy

    def _expand(self, node):
        """Développe un nœud : calcule les probabilités pour chaque coup légal."""
        state = node.state
        if is_game_over(state):
            return get_winner(state) * state.current_player  # valeur terminale

        value, log_policy = self._evaluate(state)
        moves = legal_moves(state)

        # Extraire les probabilités pour les coups légaux
        indices = [move_to_index(m) for m in moves]
        raw     = np.array([log_policy[i] for i in indices])
        raw    -= raw.max()
        priors  = np.exp(raw)
        priors /= priors.sum()

        # Bruit Dirichlet à la racine pour forcer l'exploration
        if node.parent is None and self.temperature > 0:
            noise   = np.random.dirichlet([DIRICHLET_ALPHA] * len(moves))
            priors  = (1 - DIRICHLET_EPS) * priors + DIRICHLET_EPS * noise

        for move, prior in zip(moves, priors):
            child_state = state.copy()
            child_state.apply_move(move)
            child = MCTSNode(child_state, parent=node, move=move, prior=prior)
            node.children.append(child)

        node.is_expanded = True
        return value  # valeur du point de vue du joueur COURANT

    def _select(self, node):
        """Sélectionne le meilleur enfant selon le score UCB."""
        total_visits = sum(c.N for c in node.children)
        return max(node.children, key=lambda c: c.ucb_score(total_visits))

    def run(self, root_state):
        """Lance num_simulations simulations depuis root_state."""
        root = MCTSNode(root_state.copy())

        # Expansion initiale
        self._expand(root)

        for _ in range(self.num_simulations):
            node = root

            # 1. Sélection : descendre jusqu'à une feuille
            while node.is_expanded and node.children:
                node = self._select(node)

            # 2. Expansion / évaluation
            if is_game_over(node.state):
                winner = get_winner(node.state)
                # Valeur du point de vue du joueur qui VIENT de jouer (parent.player)
                value = winner * (node.parent.player if node.parent else node.player)
                node.backup(-value)
            else:
                value = self._expand(node)
                node.backup(-value)  # On remonte l'opposé (adversaire vient de recevoir)

        return root

    def get_move_probs(self, state):
        """
        Retourne (moves, probs) — distribution de politique améliorée par MCTS.
        """
        root  = self.run(state)
        moves = [child.move for child in root.children]
        visits = np.array([child.N for child in root.children], dtype=np.float64)

        if self.temperature == 0:
            # Mode compétitif : choisir le coup le plus visité
            probs = np.zeros(len(visits))
            probs[np.argmax(visits)] = 1.0
        else:
            visits = visits ** (1.0 / self.temperature)
            probs  = visits / visits.sum()

        return moves, probs

    def select_move(self, state, _moves=None):
        """Interface compatible avec les autres agents."""
        moves, probs = self.get_move_probs(state)
        if not moves:
            return None
        return moves[np.random.choice(len(moves), p=probs)]
