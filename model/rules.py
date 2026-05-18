from model.board import EMPTY, MAN, KING


def in_bounds(r, c):
    return 0 <= r < 10 and 0 <= c < 10


# ─── Captures ──────────────────────────────────────────────────────────────

def _man_captures(board, r, c, player, captured_so_far):
    sequences = []
    for dr in [-1, 1]:
        for dc in [-1, 1]:
            mid_r, mid_c = r + dr, c + dc
            land_r, land_c = r + 2 * dr, c + 2 * dc
            if not in_bounds(land_r, land_c):
                continue
            mid_piece = board[mid_r][mid_c]
            if mid_piece == EMPTY or (mid_piece * player) > 0:
                continue
            if board[land_r][land_c] != EMPTY:
                continue
            if (mid_r, mid_c) in captured_so_far:
                continue

            board_copy = [row[:] for row in board]
            board_copy[mid_r][mid_c] = EMPTY
            board_copy[r][c] = EMPTY
            board_copy[land_r][land_c] = board[r][c]

            new_captured = captured_so_far | {(mid_r, mid_c)}
            continuations = _man_captures(board_copy, land_r, land_c, player, new_captured)

            if continuations:
                for cont in continuations:
                    sequences.append([(r, c)] + cont)
            else:
                sequences.append([(r, c), (land_r, land_c)])
    return sequences


def _king_captures(board, r, c, player, captured_so_far):
    sequences = []
    for dr in [-1, 1]:
        for dc in [-1, 1]:
            nr, nc = r + dr, c + dc
            found_target = None
            while in_bounds(nr, nc):
                p = board[nr][nc]
                if p == EMPTY:
                    if found_target and found_target not in captured_so_far:
                        land_r, land_c = nr, nc
                        board_copy = [row[:] for row in board]
                        board_copy[found_target[0]][found_target[1]] = EMPTY
                        board_copy[r][c] = EMPTY
                        board_copy[land_r][land_c] = board[r][c]

                        new_captured = captured_so_far | {found_target}
                        continuations = _king_captures(
                            board_copy, land_r, land_c, player, new_captured
                        )
                        if continuations:
                            for cont in continuations:
                                sequences.append([(r, c)] + cont)
                        else:
                            sequences.append([(r, c), (land_r, land_c)])
                elif (p * player) < 0:
                    if found_target is not None:
                        break
                    found_target = (nr, nc)
                else:
                    break
                nr += dr
                nc += dc
    return sequences


def get_captures(state):
    player = state.current_player
    board = state.board
    captures = []
    for r in range(10):
        for c in range(10):
            p = board[r][c]
            if p == EMPTY or (p * player) < 0:
                continue
            if abs(p) == MAN:
                seqs = _man_captures(board, r, c, player, set())
            else:
                seqs = _king_captures(board, r, c, player, set())
            captures.extend(seqs)
    return captures


# ─── Déplacements simples ──────────────────────────────────────────────────

def get_simple_moves(state):
    player = state.current_player
    board = state.board
    moves = []
    direction = -1 if player == 1 else 1

    for r in range(10):
        for c in range(10):
            p = board[r][c]
            if p == EMPTY or (p * player) < 0:
                continue

            if abs(p) == MAN:
                for dc in [-1, 1]:
                    nr, nc = r + direction, c + dc
                    if in_bounds(nr, nc) and board[nr][nc] == EMPTY:
                        moves.append([(r, c), (nr, nc)])

            elif abs(p) == KING:
                for dr_k in [-1, 1]:
                    for dc_k in [-1, 1]:
                        nr, nc = r + dr_k, c + dc_k
                        while in_bounds(nr, nc) and board[nr][nc] == EMPTY:
                            moves.append([(r, c), (nr, nc)])
                            nr += dr_k
                            nc += dc_k
    return moves


# ─── Coups légaux ─────────────────────────────────────────────────────────

def legal_moves(state):
    captures = get_captures(state)
    if captures:
        max_len = max(len(seq) for seq in captures)
        return [seq for seq in captures if len(seq) == max_len]
    return get_simple_moves(state)


# ─── Fin de partie ────────────────────────────────────────────────────────

def is_game_over(state):
    if state.is_draw_by_repetition():
        return True
    return len(legal_moves(state)) == 0


def get_winner(state):
    if state.is_draw_by_repetition():
        return 0
    if is_game_over(state):
        return -state.current_player
    whites, blacks = state.count_pieces()
    if whites == 0: return -1
    if blacks == 0: return 1
    return 0


def material_score(state):
    score = 0
    for r in range(10):
        for c in range(10):
            p = state.board[r][c]
            if p == MAN:     score += 1
            elif p == KING:  score += 3
            elif p == -MAN:  score -= 1
            elif p == -KING: score -= 3
    return score
