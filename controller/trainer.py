import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import os

MODEL_PATH = "models/checkpoint.pth"

def train(net, samples, epochs=5, batch_size=64, lr=1e-3, verbose=True):
    """
    Entraîne le réseau sur les samples générés par self-play.
    Chaque sample : (encoded_state [12,8,8], move_index [int], reward [float])
    """
    if not samples:
        print("Aucun sample à entraîner.")
        return

    net.train()
    optimizer = optim.Adam(net.parameters(), lr=lr, weight_decay=1e-4)
    value_criterion = nn.MSELoss()

    # Préparer les tenseurs
    states  = torch.tensor(np.stack([s[0] for s in samples]), dtype=torch.float32)
    targets = torch.tensor([s[1] for s in samples], dtype=torch.long)
    rewards = torch.tensor([s[2] for s in samples], dtype=torch.float32).unsqueeze(1)

    dataset_size = len(samples)
    indices = np.arange(dataset_size)

    for epoch in range(epochs):
        np.random.shuffle(indices)
        total_loss = 0.0
        num_batches = 0

        for start in range(0, dataset_size, batch_size):
            batch_idx = indices[start:start+batch_size]
            s_batch = states[batch_idx]
            t_batch = targets[batch_idx]
            r_batch = rewards[batch_idx]

            optimizer.zero_grad()
            value_pred, log_policy = net(s_batch)

            # Perte de valeur (MSE entre score prédit et récompense réelle)
            loss_value = value_criterion(value_pred, r_batch)

            # Perte de politique (cross-entropie entre coups prédits et coups joués)
            loss_policy = nn.NLLLoss()(log_policy, t_batch)

            loss = loss_value + loss_policy
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / max(num_batches, 1)
        if verbose:
            print(f"  Epoch {epoch+1}/{epochs} | Loss moyenne : {avg_loss:.4f}")

def save_model(net, path=MODEL_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(net.state_dict(), path)
    print(f"Modèle sauvegardé : {path}")

def load_model(net, path=MODEL_PATH):
    if os.path.exists(path):
        net.load_state_dict(torch.load(path, map_location='cpu'))
        print(f"Modèle chargé : {path}")
    else:
        print(f"Aucun checkpoint trouvé à {path}, démarrage avec poids aléatoires.")
    return net
