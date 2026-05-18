import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

EMPTY = 0
MAN   = 1
KING  = 2

PIECE_SYMBOLS = {0: '.', 1: 'b', -1: 'n', 2: 'B', -2: 'N'}


def initial_board():
    board = [[0] * 10 for _ in range(10)]
    for r in range(10):
        for c in range(10):
            if (r + c) % 2 == 1:
                if r < 4:
                    board[r][c] = -MAN
                elif r > 5:
                    board[r][c] = MAN
    return board


class BoardState:
    def __init__(self):
        self.board = initial_board()
        self.current_player = 1
        self.move_history = []
        self.no_capture_count = 0  # Pour la règle de nulle

    def copy(self):
        new = BoardState.__new__(BoardState)
        new.board = [row[:] for row in self.board]
        new.current_player = self.current_player
        new.move_history = self.move_history[:]
        new.no_capture_count = self.no_capture_count
        return new

    def apply_move(self, move):
        self.move_history.append((move, self.current_player))
        path = move
        r0, c0 = path[0]
        piece = self.board[r0][c0]
        captured = False

        for i in range(len(path) - 1):
            r1, c1 = path[i]
            r2, c2 = path[i + 1]
            mid_r = (r1 + r2) // 2
            mid_c = (c1 + c2) // 2
            if abs(r2 - r1) == 2:
                self.board[mid_r][mid_c] = EMPTY
                captured = True

        rf, cf = path[-1]
        self.board[rf][cf] = piece
        self.board[r0][c0] = EMPTY

        if abs(piece) == MAN:
            if piece == MAN and rf == 0:
                self.board[rf][cf] = KING
            elif piece == -MAN and rf == 9:
                self.board[rf][cf] = -KING

        self.no_capture_count = 0 if captured else self.no_capture_count + 1
        self.current_player *= -1

    def count_pieces(self):
        whites = blacks = 0
        for r in range(10):
            for c in range(10):
                p = self.board[r][c]
                if p > 0: whites += 1
                elif p < 0: blacks += 1
        return whites, blacks

    def is_draw_by_repetition(self):
        return self.no_capture_count >= 50

    def to_dict(self):
        """Sérialise pour l'API web."""
        return {
            'board': self.board,
            'current_player': self.current_player,
            'no_capture_count': self.no_capture_count,
        }

    def __repr__(self):
        lines = []
        for r in range(10):
            line = f"{r:2} "
            for c in range(10):
                line += PIECE_SYMBOLS.get(self.board[r][c], '?') + ' '
            lines.append(line)
        lines.append("   " + " ".join(str(c) for c in range(10)))
        return '\n'.join(lines)


# ─── Encodage ──────────────────────────────────────────────────────────────

def encode_board(state, from_player=None):
    """
    Tenseur (5, 10, 10) :
      0: pions joueur courant
      1: dames joueur courant
      2: pions adversaire
      3: dames adversaire
      4: plan constant = current_player (pour que le réseau sache qui joue)
    """
    player = from_player or state.current_player
    tensor = np.zeros((5, 10, 10), dtype=np.float32)
    for r in range(10):
        for c in range(10):
            p = state.board[r][c]
            if p == player * MAN:     tensor[0, r, c] = 1.0
            elif p == player * KING:  tensor[1, r, c] = 1.0
            elif p == -player * MAN:  tensor[2, r, c] = 1.0
            elif p == -player * KING: tensor[3, r, c] = 1.0
    tensor[4, :, :] = 1.0 if player == 1 else 0.0
    return tensor


# ─── Réseau ────────────────────────────────────────────────────────────────

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
    NUM_MOVES = 10 * 10 * 10 * 10  # 10 000

    def __init__(self, in_channels=5, num_filters=128, num_res_blocks=10):
        super().__init__()
        self.conv_input = nn.Conv2d(in_channels, num_filters, 3, padding=1)
        self.bn_input   = nn.BatchNorm2d(num_filters)
        self.res_blocks = nn.Sequential(
            *[ResidualBlock(num_filters) for _ in range(num_res_blocks)]
        )
        # Value head
        self.value_conv = nn.Conv2d(num_filters, 1, 1)
        self.value_bn   = nn.BatchNorm2d(1)
        self.value_fc1  = nn.Linear(100, 256)
        self.value_fc2  = nn.Linear(256, 1)
        # Policy head
        self.policy_conv = nn.Conv2d(num_filters, 2, 1)
        self.policy_bn   = nn.BatchNorm2d(2)
        self.policy_fc   = nn.Linear(200, self.NUM_MOVES)

    def forward(self, x):
        x = F.relu(self.bn_input(self.conv_input(x)))
        x = self.res_blocks(x)

        v = F.relu(self.value_bn(self.value_conv(x)))
        v = v.view(v.size(0), -1)
        v = F.relu(self.value_fc1(v))
        v = torch.tanh(self.value_fc2(v))

        p = F.relu(self.policy_bn(self.policy_conv(x)))
        p = p.view(p.size(0), -1)
        p = self.policy_fc(p)
        p = F.log_softmax(p, dim=1)

        return v, p


def move_to_index(move):
    r0, c0 = move[0]
    rf, cf = move[-1]
    return (r0 * 10 + c0) * 100 + (rf * 10 + cf)
