<<<<<<< HEAD
♟️ README — Projet Python : Système d’Apprentissage pour un Jeu d’Échecs
📌 Description

Ce projet a pour objectif de créer un système d’apprentissage automatique permettant à un ordinateur de jouer aux échecs.
Le programme utilise Python pour entraîner une intelligence artificielle capable d’analyser des positions, apprendre des stratégies et améliorer son niveau de jeu au fil des parties.
=======
# CheckersMind — Jeu de dames avec apprentissage par renforcement

Moteur de jeu de dames 10×10 (règles internationales) en Python, avec entraînement AlphaZero-style.
>>>>>>> 4d4ea74bdce82990b322403496f2fdcad8c0d8a4

Le projet peut évoluer vers :

<<<<<<< HEAD
un moteur d’échecs simple,
un système basé sur le machine learning,
ou une IA utilisant du reinforcement learning.
=======
```bash
pip install torch numpy
```
>>>>>>> 4d4ea74bdce82990b322403496f2fdcad8c0d8a4


<<<<<<< HEAD
 Fonctionnalités :
Génération et gestion du plateau d’échecs
Validation des coups
Système de parties IA vs IA
Enregistrement des parties
Évaluation des positions
Entraînement automatique du modèle
Possibilité d’affronter l’IA
Support des modèles d’apprentissage


 Technologies utilisées :
Python 3.x
Bibliothèque python-chess
NumPy
PyTorch ou TensorFlow
Matplotlib
Stockfish (optionnel pour l’analyse)
=======
Depuis le dossier `checkersmind/` :

```bash
python main.py train    # Entraîner l'IA par self-play
python main.py play     # Jouer contre l'IA (vous = blancs)
python main.py watch    # Regarder l'IA jouer contre elle-même
python main.py random   # Partie aléatoire (test des règles)
```

## Notation des coups

`(ligne,col)-(ligne,col)` — les cases sont numérotées de (0,0) en haut à gauche à (9,9) en bas à droite.  
Seules les cases sombres sont jouables (r+c impair).

- Déplacement simple : `(8,1)-(7,2)`
- Rafle : `(8,1)-(6,3)-(4,5)`

## Structure

```
checkersmind/
├── model/
│   ├── board.py      # Plateau 10x10, pièces, encodage, réseau (CheckersNet)
│   └── rules.py      # Génération des coups, prises obligatoires, rafles
├── view/
│   └── terminal_view.py
├── controller/
│   ├── game.py
│   ├── self_play.py
│   └── trainer.py
├── models/           # Poids sauvegardés (checkpoint.pth)
└── main.py
```

## Règles implémentées

- Plateau 10×10, 20 pions par camp
- Prises **obligatoires** (capture forcée)
- Prise **maximale** (on doit prendre le plus de pièces possible)
- **Rafle** complète (enchaînement de prises)
- **Promotion** en dame (fin de diagonale opposée)
- **Dame volante** : glisse sur toute la diagonale, capture à distance

## Réseau de neurones

- Entrée : tenseur (4, 10, 10) — pions blancs, dames blanches, pions noirs, dames noires
- Tronc : 1 convolution + 6 blocs résiduels (64 filtres)
- Tête valeur : score [-1, 1]
- Tête politique : distribution sur 10 000 coups encodés (case départ × case arrivée)
>>>>>>> 4d4ea74bdce82990b322403496f2fdcad8c0d8a4
