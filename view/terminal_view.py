from model.board import PIECE_SYMBOLS

def display_board(state):
    print()
    for row in reversed(range(8)):
        line = f" {row+1} |"
        for col in range(8):
            piece = state.board[row][col]
            symbol = PIECE_SYMBOLS.get(piece, '?')
            # Fond alterné simulé avec espaces
            line += f" {symbol} "
        print(line)
    print("    " + "---"*8)
    print("     a  b  c  d  e  f  g  h")
    player_str = "Blancs" if state.current_player == 1 else "Noirs"
    print(f"\nTrait aux {player_str} | Coup n°{state.fullmove_number}")
    print()

def display_result(result):
    if result == 1:
        print("=== Les BLANCS gagnent ! ===")
    elif result == -1:
        print("=== Les NOIRS gagnent ! ===")
    else:
        print("=== NULLE ===")

def move_to_notation(move):
    """Convertit un coup interne en notation algébrique simple (ex. e2e4)."""
    (fr, fc), (tr, tc), promo = move
    cols = 'abcdefgh'
    notation = f"{cols[fc]}{fr+1}{cols[tc]}{tr+1}"
    if promo:
        promo_sym = {5:'q', 4:'r', 3:'b', 2:'n'}
        notation += promo_sym.get(promo, 'q')
    return notation

def notation_to_move(notation, legal_moves_list):
    """Tente de convertir une notation algébrique en coup légal."""
    cols = 'abcdefgh'
    if len(notation) < 4:
        return None
    try:
        fc = cols.index(notation[0])
        fr = int(notation[1]) - 1
        tc = cols.index(notation[2])
        tr = int(notation[3]) - 1
    except (ValueError, IndexError):
        return None
    promo = None
    if len(notation) == 5:
        promo_map = {'q': 5, 'r': 4, 'b': 3, 'n': 2}
        promo = promo_map.get(notation[4].lower())

    for move in legal_moves_list:
        (mfr, mfc), (mtr, mtc), mpromo = move
        if mfr == fr and mfc == fc and mtr == tr and mtc == tc:
            if promo is None or mpromo == promo:
                return move
    return None
