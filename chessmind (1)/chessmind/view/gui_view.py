try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

from model.board import PIECE_SYMBOLS

SQUARE_SIZE = 80
WIDTH = HEIGHT = SQUARE_SIZE * 8

LIGHT = (240, 217, 181)
DARK  = (181, 136,  99)
HIGHLIGHT = (186, 202,  68)
TEXT_COLOR = (50, 50, 50)

UNICODE_PIECES = {
    6: '♔', -6: '♚',
    5: '♕', -5: '♛',
    4: '♖', -4: '♜',
    3: '♗', -3: '♝',
    2: '♘', -2: '♞',
    1: '♙', -1: '♟',
}

class GUIView:
    def __init__(self):
        if not PYGAME_AVAILABLE:
            raise RuntimeError("pygame n'est pas installé. Lancez : pip install pygame")
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT + 40))
        pygame.display.set_caption("ChessMind")
        self.font_pieces = pygame.font.SysFont("segoeuisymbol", 56)
        self.font_info = pygame.font.SysFont("monospace", 18)
        self.selected = None
        self.highlights = []

    def draw(self, state, legal_moves_list=None):
        self.screen.fill((30, 30, 30))
        for row in range(8):
            for col in range(8):
                color = LIGHT if (row + col) % 2 == 0 else DARK
                x = col * SQUARE_SIZE
                y = (7 - row) * SQUARE_SIZE
                rect = pygame.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)
                pygame.draw.rect(self.screen, color, rect)

                # Surlignage des coups légaux
                if legal_moves_list:
                    for move in legal_moves_list:
                        (fr, fc), (tr, tc), _ = move
                        if (tr, tc) == (row, col):
                            pygame.draw.rect(self.screen, HIGHLIGHT, rect, 4)

                piece = state.board[row][col]
                if piece != 0:
                    symbol = UNICODE_PIECES.get(piece, '')
                    color_piece = (255, 255, 255) if piece > 0 else (20, 20, 20)
                    surf = self.font_pieces.render(symbol, True, color_piece)
                    self.screen.blit(surf, (x + 10, y + 8))

        # Barre d'information
        player_str = "Blancs" if state.current_player == 1 else "Noirs"
        info = self.font_info.render(f"Trait aux {player_str}  |  Coup {state.fullmove_number}", True, (220, 220, 220))
        self.screen.blit(info, (10, HEIGHT + 8))

        pygame.display.flip()

    def get_clicked_square(self, pos):
        x, y = pos
        col = x // SQUARE_SIZE
        row = 7 - (y // SQUARE_SIZE)
        if 0 <= row < 8 and 0 <= col < 8:
            return row, col
        return None

    def wait_for_move(self, state, legal_moves_list):
        """Boucle d'attente d'un coup humain via clic."""
        from_sq = None
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.MOUSEBUTTONDOWN:
                    sq = self.get_clicked_square(event.pos)
                    if sq is None:
                        continue
                    if from_sq is None:
                        # Sélection de la pièce
                        piece = state.board[sq[0]][sq[1]]
                        if piece != 0 and (piece > 0) == (state.current_player > 0):
                            from_sq = sq
                            self.highlights = [m for m in legal_moves_list if m[0] == from_sq]
                            self.draw(state, self.highlights)
                    else:
                        # Destination
                        for move in legal_moves_list:
                            if move[0] == from_sq and move[1] == sq:
                                self.highlights = []
                                return move
                        from_sq = None
                        self.highlights = []
                        self.draw(state)

    def close(self):
        if PYGAME_AVAILABLE:
            pygame.quit()
