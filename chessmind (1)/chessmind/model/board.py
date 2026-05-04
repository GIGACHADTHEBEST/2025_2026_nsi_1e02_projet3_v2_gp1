import copy

# Pièces : positif = blancs, négatif = noirs
EMPTY = 0
PAWN   = 1
KNIGHT = 2
BISHOP = 3
ROOK   = 4
QUEEN  = 5
KING   = 6

PIECE_SYMBOLS = {
    0: '.',
    1: 'P', -1: 'p',
    2: 'N', -2: 'n',
    3: 'B', -3: 'b',
    4: 'R', -4: 'r',
    5: 'Q', -5: 'q',
    6: 'K', -6: 'k',
}

def initial_board():
    board = [[0]*8 for _ in range(8)]
    # Pièces blanches (rangée 0 et 1)
    back_row = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]
    for col, piece in enumerate(back_row):
        board[0][col] = piece
        board[1][col] = PAWN
    # Pièces noires (rangée 7 et 6)
    for col, piece in enumerate(back_row):
        board[7][col] = -piece
        board[6][col] = -PAWN
    return board

class BoardState:
    def __init__(self):
        self.board = initial_board()
        self.current_player = 1  # 1 = blancs, -1 = noirs
        self.castling_rights = {
            'K': True, 'Q': True,   # blancs
            'k': True, 'q': True,   # noirs
        }
        self.en_passant_target = None  # case cible pour prise en passant
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.move_history = []

    def copy(self):
        new = BoardState.__new__(BoardState)
        new.board = [row[:] for row in self.board]
        new.current_player = self.current_player
        new.castling_rights = self.castling_rights.copy()
        new.en_passant_target = self.en_passant_target
        new.halfmove_clock = self.halfmove_clock
        new.fullmove_number = self.fullmove_number
        new.move_history = self.move_history[:]
        return new

    def get_piece(self, row, col):
        return self.board[row][col]

    def set_piece(self, row, col, piece):
        self.board[row][col] = piece

    def apply_move(self, move):
        """Applique un coup (from_sq, to_sq, promotion) sur le plateau."""
        (fr, fc), (tr, tc), promo = move
        piece = self.board[fr][fc]
        captured = self.board[tr][tc]

        self.move_history.append((move, self.castling_rights.copy(), self.en_passant_target, self.halfmove_clock))

        # Horloge des demi-coups
        if abs(piece) == PAWN or captured != EMPTY:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # Prise en passant
        new_ep = None
        if abs(piece) == PAWN and abs(tr - fr) == 2:
            new_ep = ((fr + tr) // 2, fc)

        if abs(piece) == PAWN and self.en_passant_target == (tr, tc):
            # Capturer le pion adverse
            dir = 1 if self.current_player == 1 else -1
            self.board[tr - dir][tc] = EMPTY

        # Roque
        if abs(piece) == KING:
            if fc == 4 and tc == 6:  # petit roque
                self.board[fr][5] = self.board[fr][7]
                self.board[fr][7] = EMPTY
            elif fc == 4 and tc == 2:  # grand roque
                self.board[fr][3] = self.board[fr][0]
                self.board[fr][0] = EMPTY

        # Déplacement principal
        self.board[tr][tc] = piece
        self.board[fr][fc] = EMPTY

        # Promotion
        if abs(piece) == PAWN and (tr == 7 or tr == 0):
            self.board[tr][tc] = (promo if promo else QUEEN) * self.current_player

        # Mise à jour des droits de roque
        if piece == KING:
            self.castling_rights['K'] = False
            self.castling_rights['Q'] = False
        elif piece == -KING:
            self.castling_rights['k'] = False
            self.castling_rights['q'] = False
        if (fr, fc) == (0, 7) or (tr, tc) == (0, 7): self.castling_rights['K'] = False
        if (fr, fc) == (0, 0) or (tr, tc) == (0, 0): self.castling_rights['Q'] = False
        if (fr, fc) == (7, 7) or (tr, tc) == (7, 7): self.castling_rights['k'] = False
        if (fr, fc) == (7, 0) or (tr, tc) == (7, 0): self.castling_rights['q'] = False

        self.en_passant_target = new_ep
        if self.current_player == -1:
            self.fullmove_number += 1
        self.current_player *= -1

    def __repr__(self):
        lines = []
        for row in reversed(range(8)):
            line = f"{row+1} "
            for col in range(8):
                line += PIECE_SYMBOLS.get(self.board[row][col], '?') + ' '
            lines.append(line)
        lines.append("  a b c d e f g h")
        return '\n'.join(lines)
