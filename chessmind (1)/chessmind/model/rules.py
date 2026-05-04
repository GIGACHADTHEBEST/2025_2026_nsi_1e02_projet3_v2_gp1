from model.board import EMPTY, PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING

def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def pseudo_legal_moves(state):
    """Génère tous les coups pseudo-légaux pour le joueur courant."""
    moves = []
    player = state.current_player
    board = state.board

    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == 0 or (piece > 0) != (player > 0):
                continue
            kind = abs(piece)

            if kind == PAWN:
                moves += pawn_moves(state, r, c, player)
            elif kind == KNIGHT:
                moves += knight_moves(board, r, c, player)
            elif kind == BISHOP:
                moves += sliding_moves(board, r, c, player, [(1,1),(1,-1),(-1,1),(-1,-1)])
            elif kind == ROOK:
                moves += sliding_moves(board, r, c, player, [(1,0),(-1,0),(0,1),(0,-1)])
            elif kind == QUEEN:
                moves += sliding_moves(board, r, c, player, [(1,1),(1,-1),(-1,1),(-1,-1),(1,0),(-1,0),(0,1),(0,-1)])
            elif kind == KING:
                moves += king_moves(state, r, c, player)

    return moves

def pawn_moves(state, r, c, player):
    moves = []
    board = state.board
    dir = 1 if player == 1 else -1
    start_row = 1 if player == 1 else 6
    promo_row = 7 if player == 1 else 0

    # Avance d'une case
    nr = r + dir
    if in_bounds(nr, c) and board[nr][c] == EMPTY:
        if nr == promo_row:
            for p in [QUEEN, ROOK, BISHOP, KNIGHT]:
                moves.append(((r, c), (nr, c), p))
        else:
            moves.append(((r, c), (nr, c), None))
        # Avance de deux cases depuis la position initiale
        if r == start_row and board[r + 2*dir][c] == EMPTY:
            moves.append(((r, c), (r + 2*dir, c), None))

    # Captures diagonales
    for dc in [-1, 1]:
        nc = c + dc
        nr = r + dir
        if not in_bounds(nr, nc):
            continue
        target = board[nr][nc]
        if target != EMPTY and (target > 0) != (player > 0):
            if nr == promo_row:
                for p in [QUEEN, ROOK, BISHOP, KNIGHT]:
                    moves.append(((r, c), (nr, nc), p))
            else:
                moves.append(((r, c), (nr, nc), None))
        # Prise en passant
        if state.en_passant_target == (nr, nc):
            moves.append(((r, c), (nr, nc), None))

    return moves

def knight_moves(board, r, c, player):
    moves = []
    for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        nr, nc = r+dr, c+dc
        if in_bounds(nr, nc):
            t = board[nr][nc]
            if t == EMPTY or (t > 0) != (player > 0):
                moves.append(((r, c), (nr, nc), None))
    return moves

def sliding_moves(board, r, c, player, directions):
    moves = []
    for dr, dc in directions:
        nr, nc = r+dr, c+dc
        while in_bounds(nr, nc):
            t = board[nr][nc]
            if t == EMPTY:
                moves.append(((r, c), (nr, nc), None))
            elif (t > 0) != (player > 0):
                moves.append(((r, c), (nr, nc), None))
                break
            else:
                break
            nr += dr
            nc += dc
    return moves

def king_moves(state, r, c, player):
    board = state.board
    moves = []
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = r+dr, c+dc
            if in_bounds(nr, nc):
                t = board[nr][nc]
                if t == EMPTY or (t > 0) != (player > 0):
                    moves.append(((r, c), (nr, nc), None))

    # Roque
    if player == 1:
        if state.castling_rights['K'] and board[0][5] == EMPTY and board[0][6] == EMPTY:
            if not is_square_attacked(state, 0, 4, -1) and not is_square_attacked(state, 0, 5, -1) and not is_square_attacked(state, 0, 6, -1):
                moves.append(((0, 4), (0, 6), None))
        if state.castling_rights['Q'] and board[0][3] == EMPTY and board[0][2] == EMPTY and board[0][1] == EMPTY:
            if not is_square_attacked(state, 0, 4, -1) and not is_square_attacked(state, 0, 3, -1) and not is_square_attacked(state, 0, 2, -1):
                moves.append(((0, 4), (0, 2), None))
    else:
        if state.castling_rights['k'] and board[7][5] == EMPTY and board[7][6] == EMPTY:
            if not is_square_attacked(state, 7, 4, 1) and not is_square_attacked(state, 7, 5, 1) and not is_square_attacked(state, 7, 6, 1):
                moves.append(((7, 4), (7, 6), None))
        if state.castling_rights['q'] and board[7][3] == EMPTY and board[7][2] == EMPTY and board[7][1] == EMPTY:
            if not is_square_attacked(state, 7, 4, 1) and not is_square_attacked(state, 7, 3, 1) and not is_square_attacked(state, 7, 2, 1):
                moves.append(((7, 4), (7, 2), None))

    return moves

def is_square_attacked(state, r, c, by_player):
    """Vérifie si la case (r, c) est attaquée par by_player."""
    board = state.board

    # Attaques de cavalier
    for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
        nr, nc = r+dr, c+dc
        if in_bounds(nr, nc) and board[nr][nc] == by_player * KNIGHT:
            return True

    # Attaques de roi
    for dr in [-1,0,1]:
        for dc in [-1,0,1]:
            if dr == 0 and dc == 0: continue
            nr, nc = r+dr, c+dc
            if in_bounds(nr, nc) and board[nr][nc] == by_player * KING:
                return True

    # Attaques de pion
    pawn_dir = -1 if by_player == 1 else 1
    for dc in [-1, 1]:
        nr, nc = r+pawn_dir, c+dc
        if in_bounds(nr, nc) and board[nr][nc] == by_player * PAWN:
            return True

    # Attaques de lignes (tour, dame)
    for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
        nr, nc = r+dr, c+dc
        while in_bounds(nr, nc):
            t = board[nr][nc]
            if t != EMPTY:
                if t == by_player * ROOK or t == by_player * QUEEN:
                    return True
                break
            nr += dr; nc += dc

    # Attaques de diagonales (fou, dame)
    for dr, dc in [(1,1),(1,-1),(-1,1),(-1,-1)]:
        nr, nc = r+dr, c+dc
        while in_bounds(nr, nc):
            t = board[nr][nc]
            if t != EMPTY:
                if t == by_player * BISHOP or t == by_player * QUEEN:
                    return True
                break
            nr += dr; nc += dc

    return False

def find_king(board, player):
    for r in range(8):
        for c in range(8):
            if board[r][c] == player * KING:
                return r, c
    return None

def is_in_check(state, player):
    kr, kc = find_king(state.board, player)
    return is_square_attacked(state, kr, kc, -player)

def legal_moves(state):
    """Retourne uniquement les coups légaux (ne laissant pas le roi en échec)."""
    moves = []
    for move in pseudo_legal_moves(state):
        new_state = state.copy()
        new_state.apply_move(move)
        # Après le coup, vérifier que notre roi n'est pas en échec
        if not is_in_check(new_state, state.current_player):
            moves.append(move)
    return moves

def is_checkmate(state):
    return is_in_check(state, state.current_player) and len(legal_moves(state)) == 0

def is_stalemate(state):
    return not is_in_check(state, state.current_player) and len(legal_moves(state)) == 0

def is_draw(state):
    """Détecte nulle par règle des 50 coups ou pat."""
    return state.halfmove_clock >= 100 or is_stalemate(state)
