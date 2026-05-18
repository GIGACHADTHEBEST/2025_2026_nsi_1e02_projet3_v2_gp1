import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

def encode_board(state):
    """
    Encode le plateau en tenseur (12, 8, 8) :
    - 6 plans pour les pièces blanches (pion, cavalier, fou, tour, dame, roi)
    - 6 plans pour les pièces noires
    Valeur 1.0 si la pièce est présente, 0.0 sinon.
    """
    tensor = np.zeros((12, 8, 8), dtype=np.float32)
    piece_to_plane = {1:0, 2:1, 3:2, 4:3, 5:4, 6:5}
    for r in range(8):
        for c in range(8):
            p = state.board[r][c]
            if p > 0:
                tensor[piece_to_plane[p], r, c] = 1.0
            elif p < 0:
                tensor[6 + piece_to_plane[-p], r, c] = 1.0
    return tensor

def encode_board_batch(states):
    return np.stack([encode_board(s) for s in states])

class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x):
        residual = x
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.bn2(self.conv2(x))
        return F.relu(x + residual)

class ChessNet(nn.Module):
    """
    Réseau inspiré d'AlphaZero :
    - Tronc commun : convolution + blocs résiduels
    - Tête de valeur : prédit le score de la position [-1, 1]
    - Tête de politique : prédit les probabilités de chaque coup (4096 = 64*64)
    """
    def __init__(self, in_channels=12, num_filters=64, num_res_blocks=5):
        super().__init__()

        # Tronc
        self.conv_input = nn.Conv2d(in_channels, num_filters, 3, padding=1)
        self.bn_input = nn.BatchNorm2d(num_filters)
        self.res_blocks = nn.Sequential(*[ResidualBlock(num_filters) for _ in range(num_res_blocks)])

        # Tête de valeur
        self.value_conv = nn.Conv2d(num_filters, 1, 1)
        self.value_bn = nn.BatchNorm2d(1)
        self.value_fc1 = nn.Linear(64, 64)
        self.value_fc2 = nn.Linear(64, 1)

        # Tête de politique
        self.policy_conv = nn.Conv2d(num_filters, 2, 1)
        self.policy_bn = nn.BatchNorm2d(2)
        self.policy_fc = nn.Linear(2 * 64, 4096)  # 64*64 coups possibles

    def forward(self, x):
        # Tronc commun
        x = F.relu(self.bn_input(self.conv_input(x)))
        x = self.res_blocks(x)

        # Tête de valeur
        v = F.relu(self.value_bn(self.value_conv(x)))
        v = v.view(v.size(0), -1)
        v = F.relu(self.value_fc1(v))
        v = torch.tanh(self.value_fc2(v))  # score entre -1 et 1

        # Tête de politique
        p = F.relu(self.policy_bn(self.policy_conv(x)))
        p = p.view(p.size(0), -1)
        p = self.policy_fc(p)
        p = F.log_softmax(p, dim=1)

        return v, p

def move_to_index(move):
    """Convertit un coup (from, to, promo) en index 0-4095."""
    (fr, fc), (tr, tc), _ = move
    return (fr * 8 + fc) * 64 + (tr * 8 + tc)

def index_to_squares(idx):
    from_idx = idx // 64
    to_idx = idx % 64
    return (from_idx // 8, from_idx % 8), (to_idx // 8, to_idx % 8)
