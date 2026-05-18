import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# Pièces : positif = blancs, négatif = noirs
EMPTY  = 0
MAN    = 1   # pion normal
KING   = 2   # dame

PIECE_SYMBOLS = {
    0: '.', 1: 'b', -1: 'n', 2: 'B', -2: 'N'
}

def initial_board():
    """Plateau de dames 10x10 (règles internationales)."""
    board = [[0] * 10 for _ in range(10)]
    # Les pièces occupent uniquement les cases sombres (r+c impair)
    for r in range(10):
        for c in range(10):
            if (r + c) % 2 == 1:
                if r < 4:
                    board[r][c] = -MAN   # noirs en haut (rangées 0-3)
                elif r > 5:
                    board[r][c] = MAN    # blancs en bas (rangées 6-9)
    return board

class BoardState:
    def __init__(self):
        self.board = initial_board()
        self.current_player = 1   # 1 = blancs, -1 = noirs
        self.move_history = []

    def copy(self):
        new = BoardState.__new__(BoardState)
        new.board = [row[:] for row in self.board]
        new.current_player = self.current_player
        new.move_history = self.move_history[:]
        return new

    def apply_move(self, move):
        """
        Un coup est une liste de cases : [(r0,c0), (r1,c1), ...]
        - Déplacement simple : 2 cases
        - Rafle : 3+ cases (toutes les cases traversées)
        """
        self.move_history.append((move, self.current_player))
        path = move
        r0, c0 = path[0]
        piece = self.board[r0][c0]

        # Supprimer les pièces capturées entre chaque étape
        for i in range(len(path) - 1):
            r1, c1 = path[i]
            r2, c2 = path[i + 1]
            mid_r = (r1 + r2) // 2
            mid_c = (c1 + c2) // 2
            if abs(r2 - r1) == 2:   # saut = capture
                self.board[mid_r][mid_c] = EMPTY

        # Déplacer la pièce à la destination finale
        rf, cf = path[-1]
        self.board[rf][cf] = piece
        self.board[r0][c0] = EMPTY

        # Promotion en dame
        if abs(piece) == MAN:
            if piece == MAN and rf == 0:
                self.board[rf][cf] = KING
            elif piece == -MAN and rf == 9:
                self.board[rf][cf] = -KING

        self.current_player *= -1

    def count_pieces(self):
        whites = blacks = 0
        for r in range(10):
            for c in range(10):
                p = self.board[r][c]
                if p > 0: whites += 1
                elif p < 0: blacks += 1
        return whites, blacks

    def __repr__(self):
        lines = []
        for r in range(10):
            line = f"{r:2} "
            for c in range(10):
                line += PIECE_SYMBOLS.get(self.board[r][c], '?') + ' '
            lines.append(line)
        lines.append("   " + " ".join(str(c) for c in range(10)))
        return '\n'.join(lines)


# ─── Encodage pour le réseau de neurones ───────────────────────────────────

def encode_board(state):
    """
    Encode le plateau en tenseur (4, 10, 10) :
      Plan 0 : pions blancs
      Plan 1 : dames blanches
      Plan 2 : pions noirs
      Plan 3 : dames noires
    """
    tensor = np.zeros((4, 10, 10), dtype=np.float32)
    for r in range(10):
        for c in range(10):
            p = state.board[r][c]
            if p == MAN:    tensor[0, r, c] = 1.0
            elif p == KING: tensor[1, r, c] = 1.0
            elif p == -MAN: tensor[2, r, c] = 1.0
            elif p == -KING:tensor[3, r, c] = 1.0
    return tensor

def encode_board_batch(states):
    return np.stack([encode_board(s) for s in states])


# ─── Réseau de neurones ────────────────────────────────────────────────────

class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1)
        self.bn1   = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1)
        self.bn2   = nn.BatchNorm2d(channels)

    def forward(self, x):
        res = x
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.bn2(self.conv2(x))
        return F.relu(x + res)

class CheckersNet(nn.Module):
    """
    Réseau inspiré d'AlphaZero pour les dames 10x10.
    - Tronc : convolution + blocs résiduels
    - Tête valeur  : score de position [-1, 1]
    - Tête politique : prob. sur tous les coups encodés (100*100 = 10 000)
      (from_square * 100 + to_square, cases finales uniquement)
    """
    NUM_MOVES = 10 * 10 * 10 * 10  # 10 000 (très sparse, mais simple)

    def __init__(self, in_channels=4, num_filters=64, num_res_blocks=6):
        super().__init__()

        self.conv_input = nn.Conv2d(in_channels, num_filters, 3, padding=1)
        self.bn_input   = nn.BatchNorm2d(num_filters)
        self.res_blocks = nn.Sequential(*[ResidualBlock(num_filters) for _ in range(num_res_blocks)])

        # Tête valeur
        self.value_conv = nn.Conv2d(num_filters, 1, 1)
        self.value_bn   = nn.BatchNorm2d(1)
        self.value_fc1  = nn.Linear(100, 64)
        self.value_fc2  = nn.Linear(64, 1)

        # Tête politique
        self.policy_conv = nn.Conv2d(num_filters, 2, 1)
        self.policy_bn   = nn.BatchNorm2d(2)
        self.policy_fc   = nn.Linear(2 * 100, self.NUM_MOVES)

    def forward(self, x):
        x = F.relu(self.bn_input(self.conv_input(x)))
        x = self.res_blocks(x)

        # Valeur
        v = F.relu(self.value_bn(self.value_conv(x)))
        v = v.view(v.size(0), -1)
        v = F.relu(self.value_fc1(v))
        v = torch.tanh(self.value_fc2(v))

        # Politique
        p = F.relu(self.policy_bn(self.policy_conv(x)))
        p = p.view(p.size(0), -1)
        p = self.policy_fc(p)
        p = F.log_softmax(p, dim=1)

        return v, p


def move_to_index(move):
    """
    Encode un coup (liste de cases) par sa case de départ et d'arrivée.
    Index = (r0*10 + c0) * 100 + (rf*10 + cf)
    """
    r0, c0 = move[0]
    rf, cf = move[-1]
    return (r0 * 10 + c0) * 100 + (rf * 10 + cf)

def index_to_squares(idx):
    from_idx = idx // 100
    to_idx   = idx % 100
    return (from_idx // 10, from_idx % 10), (to_idx // 10, to_idx % 10)
