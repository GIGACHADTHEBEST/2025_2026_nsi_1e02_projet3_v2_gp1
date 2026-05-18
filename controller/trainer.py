import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from model.board import CheckersNet

MODEL_PATH  = "models/checkpoint.pth"
BEST_PATH   = "models/best.pth"


def train(net, samples, epochs=5, batch_size=64, lr=1e-3):
    """
    Entraîne le réseau sur les samples issus du self-play MCTS.
    Chaque sample : (encoded_board, policy_vector, value_target)
    - policy_vector est maintenant un vrai vecteur de distribution (MCTS),
      pas un simple index → loss de politique plus riche (KL divergence).
    """
    if not samples:
        print("  Aucun sample — entraînement ignoré.")
        return

    optimizer = optim.Adam(net.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    net.train()

    boards   = torch.tensor(np.array([s[0] for s in samples]), dtype=torch.float32)
    policies = torch.tensor(np.array([s[1] for s in samples]), dtype=torch.float32)
    values   = torch.tensor([s[2] for s in samples], dtype=torch.float32).unsqueeze(1)

    n = len(samples)
    for epoch in range(epochs):
        perm       = torch.randperm(n)
        total_loss = 0.0
        n_batches  = 0

        for start in range(0, n, batch_size):
            idx = perm[start:start + batch_size]
            bx  = boards[idx]
            bp  = policies[idx]
            bv  = values[idx]

            value_pred, log_policy_pred = net(bx)

            value_loss  = nn.MSELoss()(value_pred, bv)
            # KL(target || pred) = -sum(target * log_pred) — cible non-sparse maintenant
            policy_loss = -(bp * log_policy_pred).sum(dim=1).mean()
            loss        = value_loss + policy_loss

            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(), 1.0)  # Gradient clipping
            optimizer.step()

            total_loss += loss.item()
            n_batches  += 1

        scheduler.step()
        avg = total_loss / max(n_batches, 1)
        print(f"    Epoch {epoch + 1}/{epochs}  loss={avg:.4f}  "
              f"lr={scheduler.get_last_lr()[0]:.2e}")


def save_model(net, path=None):
    os.makedirs("models", exist_ok=True)
    p = path or MODEL_PATH
    torch.save(net.state_dict(), p)
    print(f"  Modèle sauvegardé → {p}")


def load_model(net, path=None):
    p = path or MODEL_PATH
    if os.path.exists(p):
        net.load_state_dict(torch.load(p, map_location="cpu"))
        print(f"  Modèle chargé depuis {p}")
        return True
    print("  Aucun modèle existant — démarrage à zéro.")
    return False


def evaluate_nets(net_new, net_old, n_games=20, simulations=50):
    """
    Fait jouer net_new contre net_old.
    Retourne le taux de victoire de net_new.
    Utilisé pour ne sauvegarder le meilleur modèle que si net_new est vraiment meilleur.
    """
    from model.board import BoardState
    from model.rules import is_game_over, get_winner, legal_moves
    from model.mcts import MCTS

    wins = draws = 0
    for g in range(n_games):
        state     = BoardState()
        # Alterner les couleurs pour équité
        if g % 2 == 0:
            agents = {1: MCTS(net_new, simulations, 0), -1: MCTS(net_old, simulations, 0)}
            new_color = 1
        else:
            agents = {1: MCTS(net_old, simulations, 0), -1: MCTS(net_new, simulations, 0)}
            new_color = -1

        n = 0
        while not is_game_over(state) and n < 200:
            moves = legal_moves(state)
            move  = agents[state.current_player].select_move(state)
            state.apply_move(move)
            n += 1

        winner = get_winner(state)
        if winner == new_color:
            wins += 1
        elif winner == 0:
            draws += 1

    win_rate = (wins + 0.5 * draws) / n_games
    print(f"  Évaluation : {wins}W / {draws}D / {n_games - wins - draws}L "
          f"→ taux victoire nouveau modèle = {win_rate:.1%}")
    return win_rate
