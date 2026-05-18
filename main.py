import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from board import BoardState, CheckersNet
from rules import legal_moves, is_game_over, get_winner
from self_play import run_self_play, NeuralAgent, RandomAgent
from trainer import train, save_model, load_model
from game import Game
from terminal_view import display_board, display_result, move_to_notation, notation_to_move

# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────
ITERATIONS     = 10
GAMES_PER_ITER = 50
TRAIN_EPOCHS   = 5
TEMPERATURE    = 1.0
# ──────────────────────────────────────────────

def mode_train():
    net = CheckersNet()
    load_model(net)
    print("\n=== CHECKERSMIND — MODE ENTRAÎNEMENT ===\n")
    for i in range(1, ITERATIONS + 1):
        print(f"─── Itération {i}/{ITERATIONS} ───")
        print(f"  Self-play ({GAMES_PER_ITER} parties)...")
        samples = run_self_play(net, num_games=GAMES_PER_ITER, temperature=TEMPERATURE)
        print(f"  Entraînement sur {len(samples)} positions...")
        train(net, samples, epochs=TRAIN_EPOCHS)
        save_model(net)
    print("\nEntraînement terminé.")

def mode_play():
    net = CheckersNet()
    load_model(net)
    state = BoardState()
    ai_agent = NeuralAgent(net, temperature=0)

    print("\n=== CHECKERSMIND — JOUEZ CONTRE L'IA ===")
    print("Vous jouez les BLANCS.")
    print("Notation : (ligne,col)-(ligne,col) — ex: (8,1)-(7,2)")
    print("Pour une rafle : (8,1)-(6,3)-(4,5) etc.\n")

    while True:
        display_board(state)
        moves = legal_moves(state)
        if is_game_over(state):
            display_result(get_winner(state))
            break

        if state.current_player == 1:
            while True:
                notation = input("Votre coup : ").strip()
                move = notation_to_move(notation, moves)
                if move:
                    break
                print(f"Coup invalide. Exemples : {', '.join(move_to_notation(m) for m in moves[:5])}")
        else:
            move = ai_agent.select_move(state, moves)
            print(f"L'IA joue : {move_to_notation(move)}")

        state.apply_move(move)

def mode_watch():
    net = CheckersNet()
    load_model(net)
    agent = NeuralAgent(net, temperature=0.5)
    game = Game(agent, agent)
    state = BoardState()

    print("\n=== CHECKERSMIND — IA vs IA ===\n")

    import time
    while True:
        display_board(state)
        moves = legal_moves(state)
        if is_game_over(state):
            display_result(get_winner(state))
            break
        move = agent.select_move(state, moves)
        print(f"  -> {move_to_notation(move)}")
        state.apply_move(move)
        time.sleep(0.3)

def mode_random():
    """Partie aléatoire pour tester les règles."""
    state = BoardState()
    agent = RandomAgent()
    n = 0
    while not is_game_over(state) and n < 500:
        moves = legal_moves(state)
        move = agent.select_move(state, moves)
        state.apply_move(move)
        n += 1
    display_board(state)
    display_result(get_winner(state))
    print(f"Partie terminée en {n} coups.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python main.py [train | play | watch | random]")
        print("  train  — entraîner l'IA par self-play")
        print("  play   — jouer contre l'IA (vous = blancs)")
        print("  watch  — regarder l'IA jouer contre elle-même")
        print("  random — partie aléatoire (test des règles)")
        sys.exit(0)

    mode = sys.argv[1].lower()
    if   mode == "train":  mode_train()
    elif mode == "play":   mode_play()
    elif mode == "watch":  mode_watch()
    elif mode == "random": mode_random()
    else:
        print(f"Mode inconnu : {mode}")
        sys.exit(1)
