# ♟ Jeu de Dames — Projet NSI
## Intelligence Artificielle par Q-Learning (Apprentissage par Renforcement)

---

## 🏗️ Architecture MVC

```
jeu_dames/
│
├── main.py                        ← Point d'entrée
│
├── model/
│   └── plateau.py                 ← MODÈLE : état du plateau, règles du jeu
│
├── view/
│   └── vue_principale.py          ← VUE : interface graphique Tkinter
│
├── controller/
│   └── jeu_controller.py          ← CONTRÔLEUR : logique applicative
│
└── ia/
    ├── agent_ql.py                 ← Agent Q-Learning
    └── entraineur.py              ← Entraînement par auto-jeu (self-play)
```

### Rôle de chaque composant (MVC)

| Composant | Fichier | Responsabilité |
|-----------|---------|---------------|
| **Modèle** | `model/plateau.py` | Représente l'état du jeu. Contient `Pion`, `Plateau`. Ne connaît ni la vue ni le contrôleur. |
| **Vue** | `view/vue_principale.py` | Affiche l'interface graphique. Reçoit des commandes du contrôleur. Notifie les clics. |
| **Contrôleur** | `controller/jeu_controller.py` | Fait le lien entre modèle et vue. Gère les tours, les modes de jeu, les sauvegardes. |
| **IA** | `ia/agent_ql.py` | Agent Q-Learning. Apprend à maximiser son score. |
| **Entraîneur** | `ia/entraineur.py` | Fait jouer deux IA l'une contre l'autre pour qu'elles apprennent. |

---

## 🤖 Comment fonctionne l'IA ?

### Q-Learning (Apprentissage par Renforcement)

L'IA utilise l'algorithme **Q-Learning**, une méthode d'apprentissage par renforcement sans modèle.

#### Principe fondamental
> L'IA apprend en jouant de nombreuses parties. Elle reçoit des **récompenses** selon ses actions et met à jour sa **table Q** pour prendre de meilleures décisions au fil du temps.

#### La Table Q
```
Table Q : Q[état][action] → valeur estimée
```
- **État** : représentation compacte du plateau (positions de tous les pions)
- **Action** : mouvement à jouer (chemin d'un pion)
- **Valeur** : estimation de la "récompense totale future" si on fait cette action

#### Formule de Bellman (mise à jour Q)
```
Q(s, a) ← Q(s, a) + α × [r + γ × max Q(s', a') − Q(s, a)]
```
- `α = 0.1` : taux d'apprentissage (importance des nouvelles infos)
- `γ = 0.9` : facteur de discount (importance des récompenses futures)
- `r` : récompense immédiate obtenue
- `max Q(s', a')` : meilleure valeur Q dans l'état suivant

#### Système de récompenses (objectif : maximiser les points)
| Événement | Récompense |
|-----------|-----------|
| Capturer un pion ennemi | **+1 point** |
| Capturer une dame ennemie | **+3 points** |
| Promouvoir un pion en dame | **+2 points** |
| Gagner la partie | **+10 points** |
| Perdre la partie | **−10 points** |

> ⚠️ L'IA est explicitement entraînée avec **1 pion = 1 point** comme objectif, conformément au sujet.

#### Stratégie epsilon-greedy (exploration vs exploitation)
```
ε initial = 1.0  →  100% exploration au début (coups aléatoires)
ε décroit × 0.995 par partie
ε minimum = 0.05 →  5% exploration à maturité (surtout exploitation)
```
- **Exploration** (ε élevé) : coups aléatoires → découverte de nouvelles stratégies
- **Exploitation** (ε faible) : meilleur coup connu → utilisation de l'expérience accumulée

---

## 🎮 Modes de jeu

### 1. Joueur vs IA
- Vous jouez les **Blancs**, l'IA joue les **Noirs**
- Cliquez sur un pion pour le sélectionner (surlignage jaune)
- Les cases vertes indiquent les destinations possibles
- Cliquez sur une destination pour jouer

### 2. IA vs IA (visible)
- Regardez deux IA jouer l'une contre l'autre
- Idéal pour observer la progression de l'apprentissage

### 3. Entraînement rapide
- Lance N parties en arrière-plan (sans affichage case par case)
- Permet d'entraîner l'IA sur des milliers de parties rapidement
- Les données sont sauvegardées automatiquement

---

## ▶️ Lancement

```bash
python main.py
```

**Prérequis** : Python 3.8+ avec Tkinter (inclus par défaut)

---

## 📊 Progression de l'IA

Après entraînement, l'IA améliore :
- Son **taux de victoire** (visible dans les stats)
- Son **score moyen** par partie (pions capturés)
- Le nombre d'**états connus** dans sa table Q

Les sauvegardes `save_blanc.json` et `save_noir.json` persistent entre les sessions.

---

## 📐 Règles du jeu implémentées

- Déplacements diagonaux des pions
- **Captures obligatoires** (si une capture est possible, elle doit être jouée)
- **Captures multiples** en chaîne
- Promotion en **dame** (pion atteignant le bord adverse)
- Dames : déplacement dans les 4 directions diagonales
- Victoire : adversaire sans pions ou sans mouvement possible
