# ♟ Jeu de Dames — Projet NSI
### Architecture MVC · IA Q-Learning à convergence rapide

---

## Structure du projet (MVC strict)

```
dames/
│
├── main.py                          ← Point d'entrée : assemble MVC
│
├── model/
│   └── plateau.py                   ← MODÈLE : état pur, règles, aucune dépendance
│
├── view/
│   └── vue_principale.py            ← VUE : Tkinter, interface publique seulement
│
├── controller/
│   └── jeu_controller.py            ← CONTRÔLEUR : orchestre modèle ↔ vue
│
└── ia/
    ├── agent_ql.py                  ← Agent Q-Learning (apprentissage rapide)
    └── entraineur.py               ← Auto-entraînement (self-play)
```

---

## Séparation MVC

| Couche | Fichier | Ce qu'elle FAIT | Ce qu'elle NE FAIT PAS |
|--------|---------|-----------------|------------------------|
| **Modèle** | `model/plateau.py` | État du plateau, règles, captures, promotion, score | Aucun affichage, ne connaît pas la vue |
| **Vue** | `view/vue_principale.py` | Dessine le plateau, les boutons, les stats | Aucune règle de jeu, ne touche pas au Plateau |
| **Contrôleur** | `controller/jeu_controller.py` | Gère les tours, appelle le modèle, met à jour la vue | Aucun widget Tkinter, aucune formule Q |

La vue et le modèle **ne se connaissent pas**. Seul le contrôleur fait le lien.

---

## L'IA Q-Learning — Pourquoi elle progresse vite

### Technique 1 : Hyperparamètres agressifs
```python
ALPHA      = 0.30   # taux d'apprentissage élevé
EPS_DECAY  = 0.98   # epsilon décroît rapidement (-2% par partie)
```

### Technique 2 : Reward shaping (récompenses denses)
L'IA ne reçoit pas seulement +10 à la victoire (signal trop rare).
Elle reçoit un signal à chaque coup :
```
+1.0  capturer un pion ennemi     (objectif : 1 pion = 1 point)
+3.0  capturer une dame ennemie
+2.5  promouvoir un pion en dame
+0.05 avancer vers la promotion (par rangée gagnée)
+10   gagner la partie
-10   perdre
```

### Technique 3 : Experience Replay
Les dernières 2000 transitions sont stockées.
Après chaque coup, 32 transitions aléatoires sont rejouées.
→ Les rares événements importants (captures) sont réappris plusieurs fois.

### Technique 4 : Heuristique d'initialisation
Si un état est inconnu de la table Q, sa valeur est estimée par :
```
heuristique = (mes_pions - pions_adverses) + bonus_position
```
au lieu de 0.0. Cela guide les premiers coups intelligemment.

### Formule de mise à jour (Bellman)
```
Q(s, a) ← Q(s, a) + α × [ r + γ × max Q(s', a') − Q(s, a) ]
           ─────────────────────────────────────────────────
           correction (erreur TD)
```
- `α = 0.30` : poids accordé à la nouvelle information
- `γ = 0.92` : importance des récompenses futures

---

## Lancement

```bash
cd dames
python main.py
```

**Requis** : Python 3.8+ avec Tkinter (inclus par défaut).

---

## Guide d'utilisation

| Action | Résultat |
|--------|---------|
| Cliquer sur un pion blanc | Sélection + affichage des coups légaux (vert) |
| Cliquer sur une case verte | Jouer le coup |
| Mode "IA vs IA" + Nouvelle partie | Regarder deux IA apprendre en direct |
| Entraînement rapide (500 parties) | Les IA jouent sans affichage, ~5 secondes |
| Actualiser stats | Voir taux de victoire, score moyen, états Q connus |

---

## Règles implémentées

- Déplacements diagonaux uniquement sur cases foncées
- **Captures obligatoires** (règle française)
- **Rafles** (captures multiples enchaînées)
- **Promotion** : pion atteignant le bord adverse → dame
- Dames : déplacement dans les 4 diagonales
- Victoire : adversaire sans pion OU sans mouvement légal
- **Système de points** : 1 pion = 1 pt · 1 dame = 3 pts

---

*Projet NSI — Architecture MVC · Python 3 · Tkinter · Q-Learning*
