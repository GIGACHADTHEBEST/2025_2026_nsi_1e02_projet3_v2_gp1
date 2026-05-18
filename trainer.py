import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from model.board import CheckersNet

MODEL_PATH = "models/checkpoint.pth"

def train(net, samples, epochs=5, batch_size=64, lr=1e-3):
    """Entraîne le réseau sur les samples issus du self-play."""
    if not samples:
        return

    optimizer = optim.Adam(net.parameters(), lr=lr)
    net.train()

    boards  = torch.tensor(np.array([s[0] for s in samples]), dtype=torch.float32)
    indices = torch.tensor([s[1] for s in samples], dtype=torch.long)
    results = torch.tensor([s[2] for s in samples], dtype=torch.float32).unsqueeze(1)

    dataset_size = len(samples)
    for epoch in range(epochs):
        perm = torch.randperm(dataset_size)
        total_loss = 0.0
        n_batches = 0

        for start in range(0, dataset_size, batch_size):
            idx = perm[start:start + batch_size]
            bx = boards[idx]
            bi = indices[idx]
            br = results[idx]

            value, log_policy = net(bx)

            value_loss  = nn.MSELoss()(value, br)
            policy_loss = -log_policy.gather(1, bi.unsqueeze(1)).mean()
            loss = value_loss + policy_loss

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            n_batches  += 1

        avg = total_loss / n_batches if n_batches else 0
        print(f"    Epoch {epoch+1}/{epochs}  loss={avg:.4f}")

def save_model(net):
    os.makedirs("models", exist_ok=True)
    torch.save(net.state_dict(), MODEL_PATH)
    print(f"  Modèle sauvegardé → {MODEL_PATH}")

def load_model(net):
    if os.path.exists(MODEL_PATH):
        net.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
        print(f"  Modèle chargé depuis {MODEL_PATH}")
    else:
        print("  Aucun modèle existant — démarrage à zéro.")
