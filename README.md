# CheckersMind — Dames 10×10 · AlphaZero-style

Moteur de jeu de dames internationales (10×10) avec entraînement par **self-play MCTS**,
architecture **AlphaZero**, et interface web interactive.

---

## Installation

```bash
pip install torch numpy flask
```

---

## Utilisation

```bash
# Entraîner l'IA (self-play MCTS, amélioration itérative)
python main.py train

# Jouer contre l'IA dans le terminal
python main.py play

# Regarder l'IA jouer contre elle-même (terminal)
python main.py watch

# Interface web (http://localhost:5000)
python main.py web

# Évaluer le modèle courant
python main.py eval

# Partie aléatoire (test des règles)
python main.py random
```

---

## Architecture MVC

```
checkersmind/
├── model/
│   ├── board.py       # Plateau 10x10, encodage, réseau CheckersNet (5 plans, 128 filtres, 10 blocs résiduels)
│   ├── rules.py       # Règles internationales : captures obligatoires, prise maximale, dame volante
│   └── mcts.py        # Monte Carlo Tree Search guidé par le réseau (AlphaZero-style)
├── view/
│   └── terminal_view.py
├── controller/
│   ├── game.py        # Orchestration d'une partie
│   ├── self_play.py   # Génération de données via self-play MCTS
│   └── trainer.py     # Entraînement, sauvegarde, évaluation inter-modèles
├── web/
│   ├── server.py      # API Flask
│   └── static/
│       └── index.html # Interface web (Playfair Display, thème sombre)
├── models/            # Poids sauvegardés (checkpoint.pth, best.pth)
├── requirements.txt
└── main.py
```

---

## Comment l'IA devient invincible

L'entraînement suit exactement le pipeline AlphaZero :

1. **Self-play MCTS** : l'IA joue contre elle-même en utilisant le MCTS pour générer des coups de haute qualité. Chaque position est annotée avec la distribution de visite MCTS (politique) et le résultat de la partie (valeur).

2. **Entraînement supervisé** sur ces données : le réseau apprend à reproduire la politique MCTS (tête politique) et à prédire le résultat (tête valeur).

3. **Évaluation** : le nouveau modèle affronte l'ancien. Il n'est accepté que s'il gagne ≥ 55% des parties. Sinon l'ancien est conservé.

4. **Itérations** : répéter 20+ fois. À chaque cycle, le modèle s'améliore car le self-play est guidé par un réseau plus fort.

### Paramètres clés (dans `main.py`)

| Paramètre | Défaut | Effet |
|---|---|---|
| `ITERATIONS` | 20 | Nombre de cycles d'entraînement |
| `GAMES_PER_ITER` | 30 | Parties self-play par cycle |
| `MCTS_SIMULATIONS` | 150 | Simulations MCTS par coup (↑ = plus fort) |
| `TRAIN_EPOCHS` | 10 | Epochs d'entraînement par cycle |

Pour une IA vraiment forte : augmenter `MCTS_SIMULATIONS` (400+) et `ITERATIONS` (50+).

---

## Réseau de neurones

- **Entrée** : tenseur (5, 10, 10) — pions/dames du joueur courant, de l'adversaire, plan couleur
- **Tronc** : 1 conv + **10 blocs résiduels** (128 filtres) — plus profond que la v1
- **Tête valeur** : score [-1, 1] prédit le résultat de la partie
- **Tête politique** : distribution sur 10 000 coups (case départ × case arrivée)

---

## Règles implémentées (dames internationales)

- Plateau 10×10, 20 pions par camp
- Prises **obligatoires**
- Prise **maximale** (rafle la plus longue)
- **Dame volante** : glisse et capture à distance
- **Promotion** en dame
- Nulle par la **règle des 50 coups** sans capture
