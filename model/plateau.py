"""
MODEL : plateau.py
==================
Représente l'état du jeu de dames.
Aucune dépendance vers la vue ou le contrôleur (règle MVC stricte).

Système de points : 1 pion = 1 point, 1 dame = 3 points.
"""

from __future__ import annotations
from copy import deepcopy
from typing import List, Tuple, Optional

# ── Constantes ──────────────────────────────────────────────────────────────
VIDE       = 0
BLANC      = 1   # joueur humain
NOIR       = 2   # IA
DAME_B     = 3
DAME_N     = 4
N          = 8   # taille du plateau

VALEUR_PION  = 1
VALEUR_DAME  = 3

Chemin = List[Tuple[int, int]]


# ── Classes ──────────────────────────────────────────────────────────────────
class Pion:
    __slots__ = ("couleur", "ligne", "col", "est_dame")

    def __init__(self, couleur: int, ligne: int, col: int):
        self.couleur   = couleur
        self.ligne     = ligne
        self.col       = col
        self.est_dame  = False

    @property
    def valeur(self) -> int:
        return VALEUR_DAME if self.est_dame else VALEUR_PION

    def code_grille(self) -> int:
        if self.couleur == BLANC:
            return DAME_B if self.est_dame else BLANC
        return DAME_N if self.est_dame else NOIR

    def __repr__(self):
        t = "Dame" if self.est_dame else "Pion"
        c = "Blanc" if self.couleur == BLANC else "Noir"
        return f"{t}{c}({self.ligne},{self.col})"


class Plateau:
    """
    Modèle pur du plateau de jeu de dames.
    Contient : grille, pions, règles (mouvements, captures, promotion).
    """

    def __init__(self):
        self.grille: List[List[int]] = [[VIDE] * N for _ in range(N)]
        self.pions: dict[int, List[Pion]] = {BLANC: [], NOIR: []}
        self._initialiser()

    # ── Initialisation ──────────────────────────────────────────────────────
    def _initialiser(self):
        for l in range(3):
            for c in range(N):
                if (l + c) % 2 == 1:
                    p = Pion(NOIR, l, c)
                    self.pions[NOIR].append(p)
                    self.grille[l][c] = NOIR
        for l in range(5, N):
            for c in range(N):
                if (l + c) % 2 == 1:
                    p = Pion(BLANC, l, c)
                    self.pions[BLANC].append(p)
                    self.grille[l][c] = BLANC

    # ── Accesseurs ──────────────────────────────────────────────────────────
    def pion_en(self, l: int, c: int) -> Optional[Pion]:
        for couleur in (BLANC, NOIR):
            for p in self.pions[couleur]:
                if p.ligne == l and p.col == c:
                    return p
        return None

    def score(self, couleur: int) -> int:
        """Score = somme des valeurs des pions restants."""
        return sum(p.valeur for p in self.pions[couleur])

    # ── Mouvements légaux ───────────────────────────────────────────────────
    def mouvements_legaux(self, couleur: int) -> List[Tuple[Pion, Chemin]]:
        """
        Retourne tous les mouvements légaux pour une couleur.
        Les captures sont OBLIGATOIRES (prioritaires sur les déplacements simples).
        """
        captures = self._toutes_captures(couleur)
        if captures:
            return captures
        return self._tous_deplacement_simples(couleur)

    def _tous_deplacement_simples(self, couleur: int) -> List[Tuple[Pion, Chemin]]:
        res = []
        fwd = -1 if couleur == BLANC else 1
        for p in self.pions[couleur]:
            dirs = [(-1,-1),(-1,1),(1,-1),(1,1)] if p.est_dame else [(fwd,-1),(fwd,1)]
            for dl, dc in dirs:
                nl, nc = p.ligne + dl, p.col + dc
                if 0 <= nl < N and 0 <= nc < N and self.grille[nl][nc] == VIDE:
                    res.append((p, [(p.ligne, p.col), (nl, nc)]))
        return res

    def _toutes_captures(self, couleur: int) -> List[Tuple[Pion, Chemin]]:
        res = []
        for p in self.pions[couleur]:
            seqs = self._captures_rec(p, p.ligne, p.col, set(),
                                       deepcopy(self.grille))
            for s in seqs:
                res.append((p, s))
        return res

    def _captures_rec(self, pion: Pion, l: int, c: int,
                       deja_cap: set, g) -> List[Chemin]:
        adverse = NOIR if pion.couleur == BLANC else BLANC
        fwd = -1 if pion.couleur == BLANC else 1
        dirs = [(-1,-1),(-1,1),(1,-1),(1,1)] if pion.est_dame else \
               [(fwd,-1),(fwd,1),(-fwd,-1),(-fwd,1)]
        res = []
        for dl, dc in dirs:
            ml, mc = l+dl, c+dc        # case à sauter
            al, ac = l+2*dl, c+2*dc    # case d'arrivée
            if not (0<=ml<N and 0<=mc<N and 0<=al<N and 0<=ac<N):
                continue
            case_m = g[ml][mc]
            est_adv = (case_m == adverse
                       or (adverse == NOIR  and case_m == DAME_N)
                       or (adverse == BLANC and case_m == DAME_B))
            if est_adv and g[al][ac] == VIDE and (ml,mc) not in deja_cap:
                g2 = deepcopy(g)
                g2[ml][mc] = VIDE
                g2[l][c]   = VIDE
                g2[al][ac] = pion.code_grille()
                suite = self._captures_rec(pion, al, ac, deja_cap|{(ml,mc)}, g2)
                if suite:
                    for s in suite:
                        res.append([(l,c)] + s)
                else:
                    res.append([(l,c), (al,ac)])
        return res

    # ── Application d'un mouvement ──────────────────────────────────────────
    def appliquer(self, pion: Pion, chemin: Chemin) -> List[Pion]:
        """
        Joue le mouvement. Retourne la liste des pions capturés.
        Met à jour la grille et les listes de pions.
        """
        captures: List[Pion] = []
        for i in range(len(chemin) - 1):
            l1, c1 = chemin[i]
            l2, c2 = chemin[i+1]
            # Si saut : capturer le pion intermédiaire
            if abs(l2-l1) == 2:
                ml, mc = (l1+l2)//2, (c1+c2)//2
                cap = self.pion_en(ml, mc)
                if cap:
                    captures.append(cap)
                    self.pions[cap.couleur].remove(cap)
                    self.grille[ml][mc] = VIDE

        self.grille[pion.ligne][pion.col] = VIDE
        pion.ligne, pion.col = chemin[-1]

        # Promotion
        if pion.couleur == BLANC and pion.ligne == 0 and not pion.est_dame:
            pion.est_dame = True
        elif pion.couleur == NOIR and pion.ligne == N-1 and not pion.est_dame:
            pion.est_dame = True

        self.grille[pion.ligne][pion.col] = pion.code_grille()
        return captures

    # ── Fin de partie ───────────────────────────────────────────────────────
    def gagnant(self) -> int:
        """Retourne BLANC, NOIR, ou 0 si la partie continue."""
        if not self.pions[BLANC] or not self.mouvements_legaux(BLANC):
            return NOIR
        if not self.pions[NOIR]  or not self.mouvements_legaux(NOIR):
            return BLANC
        return 0

    # ── Copie profonde ──────────────────────────────────────────────────────
    def copie(self) -> "Plateau":
        p = Plateau.__new__(Plateau)
        p.grille = deepcopy(self.grille)
        p.pions  = {
            BLANC: [deepcopy(x) for x in self.pions[BLANC]],
            NOIR:  [deepcopy(x) for x in self.pions[NOIR]],
        }
        return p

    def cle(self) -> str:
        """Représentation compacte du plateau (clé pour la table Q)."""
        parts = []
        for l in range(N):
            for c in range(N):
                v = self.grille[l][c]
                if v:
                    parts.append(f"{l}{c}{v}")
        return "|".join(parts)
