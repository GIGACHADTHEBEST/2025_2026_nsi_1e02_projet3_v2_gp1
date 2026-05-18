"""
CheckersMind — Point d'entrée principal
Usage : python main.py [train | play | watch | random | web | eval]
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from model.board import BoardState, CheckersNet
from model.rules import legal_moves, is_game_over, get_winner
from controller.self_play import run_self_play, NeuralAgent, MCTSAgent, RandomAgent
from controller.trainer import train, save_model, load_model, evaluate_nets, BEST_PATH
from controller.game import Game
from view.terminal_view import display_board, display_result, move_to_notation, notation_to_move

# ─── Configuration ────────────────────────────────────────────────────────
ITERATIONS          = 20    # Nombre de cycles self-play → train
GAMES_PER_ITER      = 30    # Parties self-play par itération
MCTS_SIMULATIONS    = 150   # Simulations MCTS par coup (+ = plus fort, + = plus lent)
TRAIN_EPOCHS        = 10
TEMPERATURE_TRAIN   = 1.2   # Haute température → exploration diverse
ACCEPT_THRESHOLD    = 0.55  # Taux victoire pour accepter le nouveau modèle


def mode_train():
    net = CheckersNet()
    load_model(net)
    print("\n=== CheckersMind — ENTRAÎNEMENT MCTS-AlphaZero ===\n")
    print(f"  {ITERATIONS} itérations × {GAMES_PER_ITER} parties × {MCTS_SIMULATIONS} simulations MCTS\n")

    for i in range(1, ITERATIONS + 1):
        print(f"─── Itération {i}/{ITERATIONS} ───")
        print(f"  Self-play avec MCTS ({GAMES_PER_ITER} parties, {MCTS_SIMULATIONS} sims/coup)...")

        samples = run_self_play(
            net,
            num_games=GAMES_PER_ITER,
            num_simulations=MCTS_SIMULATIONS,
            temperature=TEMPERATURE_TRAIN,
        )
        print(f"  {len(samples)} positions générées")

        # Sauvegarder l'ancien modèle pour évaluation
        import copy, torch
        net_old = CheckersNet()
        net_old.load_state_dict(copy.deepcopy(net.state_dict()))

        print(f"  Entraînement ({TRAIN_EPOCHS} epochs)...")
        train(net, samples, epochs=TRAIN_EPOCHS)

        # Évaluation : le nouveau modèle est-il meilleur ?
        print("  Évaluation nouveau vs ancien...")
        win_rate = evaluate_nets(net, net_old, n_games=10, simulations=50)

        if win_rate >= ACCEPT_THRESHOLD:
            save_model(net)
            save_model(net, BEST_PATH)
            print(f"  ✓ Nouveau modèle accepté (taux = {win_rate:.1%})")
        else:
            # Revenir à l'ancien
            net.load_state_dict(net_old.state_dict())
            save_model(net)
            print(f"  ✗ Nouveau modèle rejeté — conservation de l'ancien")

    print("\nEntraînement terminé. L'IA a progressé !")


def mode_play():
    net = CheckersNet()
    load_model(net)
    state    = BoardState()
    ai_agent = MCTSAgent(net, num_simulations=200, temperature=0)

    print("\n=== CheckersMind — JOUEZ CONTRE L'IA ===")
    print("Vous jouez les BLANCS (jouent en premier).")
    print("Notation : (ligne,col)-(ligne,col) — ex: (8,1)-(7,2)")
    print("Rafle    : (8,1)-(6,3)-(4,5)\n")

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
                examples = ', '.join(move_to_notation(m) for m in moves[:4])
                print(f"  Coup invalide. Exemples : {examples}")
        else:
            print("  L'IA réfléchit...")
            move = ai_agent.select_move(state, moves)
            print(f"  IA joue : {move_to_notation(move)}")

        state.apply_move(move)


def mode_watch():
    """IA vs IA avec affichage terminal."""
    net   = CheckersNet()
    load_model(net)
    agent = MCTSAgent(net, num_simulations=100, temperature=0.3)
    state = BoardState()

    print("\n=== CheckersMind — IA vs IA ===\n")

    import time
    while True:
        display_board(state)
        if is_game_over(state):
            display_result(get_winner(state))
            break
        move = agent.select_move(state)
        print(f"  -> {move_to_notation(move)}")
        state.apply_move(move)
        time.sleep(0.2)


def mode_random():
    """Partie aléatoire pour tester les règles."""
    state = BoardState()
    agent = RandomAgent()
    n = 0
    while not is_game_over(state) and n < 500:
        moves = legal_moves(state)
        move  = agent.select_move(state, moves)
        state.apply_move(move)
        n += 1
    display_board(state)
    display_result(get_winner(state))
    print(f"Partie terminée en {n} coups.")


def mode_eval():
    """Évalue le modèle courant vs un agent aléatoire."""
    import torch, copy
    net = CheckersNet()
    if not load_model(net):
        print("Aucun modèle — lancez d'abord python main.py train")
        return
    net_random = CheckersNet()  # Réseau non entraîné ≈ aléatoire
    win_rate = evaluate_nets(net, net_random, n_games=20, simulations=50)
    print(f"\nTaux victoire vs réseau vierge : {win_rate:.1%}")
    if win_rate > 0.8:
        print("L'IA est clairement meilleure qu'un joueur aléatoire.")


def mode_web():
    """Lance l'interface web Flask."""
    try:
        import flask
    except ImportError:
        print("Flask manquant. Installez-le : pip install flask")
        return
    sys.path.insert(0, os.path.dirname(__file__))
    os.chdir(os.path.dirname(__file__))
    from web.server import app
    print("\n  CheckersMind — Interface Web")
    print("  Ouvrez http://localhost:5000 dans votre navigateur\n")
    app.run(debug=False, port=5000)


# ─── Dispatch ─────────────────────────────────────────────────────────────
MODES = {
    'train':  mode_train,
    'play':   mode_play,
    'watch':  mode_watch,
    'random': mode_random,
    'eval':   mode_eval,
    'web':    mode_web,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in MODES:
        print("\nUsage : python main.py [mode]\n")
        print("  train  — entraîner l'IA par self-play MCTS (AlphaZero-style)")
        print("  play   — jouer contre l'IA dans le terminal")
        print("  watch  — regarder l'IA jouer contre elle-même")
        print("  random — partie aléatoire (test des règles)")
        print("  eval   — évaluer le modèle courant")
        print("  web    — lancer l'interface web (http://localhost:5000)\n")
        sys.exit(0)

    MODES[sys.argv[1]]()
