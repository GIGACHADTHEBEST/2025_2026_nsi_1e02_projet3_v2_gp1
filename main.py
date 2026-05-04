import sys
import os

# Permet les imports depuis la racine du projet
sys.path.insert(0, os.path.dirname(__file__))

from model.neural_net import ChessNet
from controller.self_play import run_self_play, NeuralAgent, RandomAgent
from controller.trainer import train, save_model, load_model
from controller.game import Game
from view.terminal_view import display_board, display_result, move_to_notation, notation_to_move
from model.rules import legal_moves

# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────
ITERATIONS       = 10      # Nombre de cycles entraînement
GAMES_PER_ITER   = 50      # Parties de self-play par itération
TRAIN_EPOCHS     = 5       # Epochs d'entraînement par itération
TEMPERATURE      = 1.0     # Exploration pendant le self-play
# ──────────────────────────────────────────────

def mode_train():
    """Entraînement en boucle par self-play."""
    net = ChessNet()
    load_model(net)

    print("\n=== CHESSMIND — MODE ENTRAÎNEMENT ===\n")

    for i in range(1, ITERATIONS + 1):
        print(f"─── Itération {i}/{ITERATIONS} ───")

        print(f"  Self-play ({GAMES_PER_ITER} parties)...")
        samples = run_self_play(net, num_games=GAMES_PER_ITER, temperature=TEMPERATURE)

        print(f"  Entraînement sur {len(samples)} samples...")
        train(net, samples, epochs=TRAIN_EPOCHS)

        save_model(net)

    print("\nEntraînement terminé.")

def mode_play():
    """Jouer contre l'IA en terminal."""
    net = ChessNet()
    load_model(net)

    from model.board import BoardState
    state = BoardState()

    # L'humain joue les blancs, l'IA les noirs
    ai_agent = NeuralAgent(net, temperature=0)

    print("\n=== CHESSMIND — JOUEZ CONTRE L'IA ===")
    print("Entrez vos coups en notation algébrique (ex: e2e4, g1f3, e7e8q pour promotion)\n")

    while True:
        display_board(state)
        moves = legal_moves(state)

        from model.rules import is_checkmate, is_draw
        if is_checkmate(state):
            display_result(-state.current_player)
            break
        if is_draw(state):
            display_result(0)
            break

        if state.current_player == 1:
            # Tour de l'humain
            while True:
                notation = input("Votre coup : ").strip().lower()
                move = notation_to_move(notation, moves)
                if move:
                    break
                print(f"Coup invalide. Coups légaux : {', '.join(move_to_notation(m) for m in moves[:10])}...")
        else:
            # Tour de l'IA
            move = ai_agent.select_move(state, moves)
            print(f"L'IA joue : {move_to_notation(move)}")

        state.apply_move(move)

def mode_watch():
    """Observer une partie IA vs IA."""
    net = ChessNet()
    load_model(net)

    agent = NeuralAgent(net, temperature=0.5)
    game = Game(agent, agent)

    from model.board import BoardState
    from model.rules import is_checkmate, is_draw
    state = BoardState()

    print("\n=== CHESSMIND — IA vs IA ===\n")

    import time
    while True:
        display_board(state)
        moves = legal_moves(state)

        if is_checkmate(state):
            display_result(-state.current_player)
            break
        if is_draw(state):
            display_result(0)
            break

        move = agent.select_move(state, moves)
        print(f"  -> {move_to_notation(move)}")
        state.apply_move(move)
        time.sleep(0.3)

def mode_gui():
    """Interface graphique pygame."""
    from view.gui_view import run_gui
    from model.neural_net import ChessNet
    from controller.trainer import load_model
    net = ChessNet()
    load_model(net)
    run_gui(net)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python main.py [train | play | watch | gui]")
        print("  train  — entraîner l'IA par self-play")
        print("  play   — jouer contre l'IA (terminal)")
        print("  watch  — regarder l'IA jouer (terminal)")
        print("  gui    — interface graphique (recommandé)")
        sys.exit(0)

    mode = sys.argv[1].lower()
    if mode == "train":
        mode_train()
    elif mode == "play":
        mode_play()
    elif mode == "watch":
        mode_watch()
    elif mode == "gui":
        mode_gui()
    else:
        print(f"Mode inconnu : {mode}")
        sys.exit(1)
