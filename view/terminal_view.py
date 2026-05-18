from model.board import PIECE_SYMBOLS


def display_board(state):
    print()
    player_name = "Blancs" if state.current_player == 1 else "Noirs"
    print(f"   {'─'*20}  Au tour des {player_name}")
    for r in range(10):
        line = f"{r:2} "
        for c in range(10):
            if (r + c) % 2 == 0:
                line += "▓▓"
            else:
                p = state.board[r][c]
                sym = PIECE_SYMBOLS.get(p, '?')
                line += f"{sym} "
        print(line)
    print("   " + " ".join(str(c) for c in range(10)))
    whites, blacks = state.count_pieces()
    print(f"   Blancs: {whites}  Noirs: {blacks}\n")


def move_to_notation(move):
    return "-".join(f"({r},{c})" for r, c in move)


def display_result(winner):
    print("\n" + "=" * 40)
    if winner == 1:
        print("  ★  Les BLANCS gagnent !")
    elif winner == -1:
        print("  ★  Les NOIRS gagnent !")
    else:
        print("  ½  Partie nulle.")
    print("=" * 40 + "\n")


def notation_to_move(notation, legal):
    try:
        parts = notation.replace("(", "").replace(")", "").split("-")
        path  = []
        for p in parts:
            nums = p.strip().split(",")
            path.append((int(nums[0]), int(nums[1])))
        for move in legal:
            if move[0] == path[0] and move[-1] == path[-1]:
                return move
    except Exception:
        pass
    return None
