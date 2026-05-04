# ChessMind

Moteur d'échecs en Python avec apprentissage par renforcement (self-play), inspiré d'AlphaZero.

## Installation

```bash
pip install torch numpy
pip install pygame  # optionnel, pour l'interface graphique
```

## Utilisation

Depuis le dossier `chessmind/` :

```bash
# Entraîner l'IA
python main.py train

# Jouer contre l'IA
python main.py play

# Regarder l'IA jouer contre elle-même
python main.py watch
```

## Structure

```
chessmind/
├── model/
│   ├── board.py         # Plateau, pièces, application des coups
│   ├── rules.py         # Génération des coups légaux (roque, e.p., promotion...)
│   └── neural_net.py    # Réseau de neurones (PyTorch) + encodage du plateau
├── view/
│   ├── terminal_view.py # Affichage ASCII
│   └── gui_view.py      # Affichage graphique pygame (optionnel)
├── controller/
│   ├── game.py          # Orchestration d'une partie
│   ├── self_play.py     # Boucle de self-play, agent neuronal, agent aléatoire
│   └── trainer.py       # Entraînement, sauvegarde, chargement du modèle
├── data/games/          # Parties sauvegardées
├── models/              # Poids du réseau (checkpoint.pth)
└── main.py              # Point d'entrée
```

## Comment ca fonctionne

1. Le réseau est initialisé avec des poids aléatoires.
2. Deux instances jouent l'une contre l'autre (self-play).
3. Le résultat de la partie est propagé sur toutes les positions jouées.
4. Le réseau s'entraîne sur ces données.
5. Le cycle recommence — la qualité de jeu augmente progressivement.

## Paramètres (dans main.py)

| Paramètre        | Défaut | Description                          |
|------------------|--------|--------------------------------------|
| ITERATIONS       | 10     | Nombre de cycles entraînement        |
| GAMES_PER_ITER   | 50     | Parties de self-play par itération   |
| TRAIN_EPOCHS     | 5      | Epochs d'entraînement par itération  |
| TEMPERATURE      | 1.0    | Exploration (0 = greedy, >0 = aléa)  |
