"""
MODEL : plateau.py
==================
Représente l'état du jeu de dames INTERNATIONALES (10×10).
Règles FMJD (Fédération Mondiale du Jeu de Dames) strictes :

  ✔ Plateau 10×10 — 20 pions par camp
  ✔ Prise obligatoire
  ✔ Prise MAXIMALE obligatoire (la rafle qui capture le plus de pions)
  ✔ Prise arrière pour les pions simples
  ✔ Dame à vol libre (se déplace sur toute une diagonale)
  ✔ Capture à vol libre (la dame saute une pièce adverse et peut s'arrêter
    sur n'importe quelle case libre derrière elle)
  ✔ Pas de promotion en cours de rafle (le pion promu continue comme pion)
  ✔ Système de points : 1 pion = 1 pt, 1 dame = 3 pts

Aucune dépendance vers la vue ou le contrôleur (règle MVC stricte).
"""

from __future__ import annotations
from copy import deepcopy
from typing import List, Tuple, Optional

# ── Constantes ──────────────────────────────────────────────────────────────
VIDE   = 0
BLANC  = 1   # joueur humain
NOIR   = 2   # IA
DAME_B = 3
DAME_N = 4
N      = 10  # plateau 10×10

VALEUR_PION = 1
VALEUR_DAME = 3

Chemin = List[Tuple[int, int]]


# ── Classes ──────────────────────────────────────────────────────────────────
class Pion:
    __slots__ = ("couleur", "ligne", "col", "est_dame")

    def __init__(self, couleur: int, ligne: int, col: int):
        self.couleur  = couleur
        self.ligne    = ligne
        self.col      = col
        self.est_dame = False

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
    Modèle pur du plateau de dames internationales (10×10 FMJD).
    """

    def __init__(self):
        self.grille: List[List[int]] = [[VIDE] * N for _ in range(N)]
        self.pions: dict[int, List[Pion]] = {BLANC: [], NOIR: []}
        self._initialiser()

    # ── Initialisation ──────────────────────────────────────────────────────
    def _initialiser(self):
        """
        Dames internationales : 4 premières rangées pour les Noirs,
        4 dernières pour les Blancs, cases foncées uniquement.
        Cases foncées = (l+c) % 2 == 1.
        """
        for l in range(4):
            for c in range(N):
                if (l + c) % 2 == 1:
                    p = Pion(NOIR, l, c)
                    self.pions[NOIR].append(p)
                    self.grille[l][c] = NOIR
        for l in range(6, N):
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
        return sum(p.valeur for p in self.pions[couleur])

    # ── Mouvements légaux ───────────────────────────────────────────────────
    def mouvements_legaux(self, couleur: int) -> List[Tuple[Pion, Chemin]]:
        """
        Règle FMJD :
        1. Si une capture est possible, elle est OBLIGATOIRE.
        2. Parmi les captures, seules les MAXIMALES sont légales
           (celles qui prennent le plus grand nombre de pièces).
        """
        captures = self._toutes_captures(couleur)
        if captures:
            # Prise maximale : ne garder que les rafles les plus longues
            max_prises = max(self._nb_prises(ch) for _, ch in captures)
            return [(p, ch) for p, ch in captures
                    if self._nb_prises(ch) == max_prises]
        return self._tous_deplacements_simples(couleur)

    @staticmethod
    def _nb_prises(chemin: Chemin) -> int:
        """Nombre de pions capturés dans un chemin (nb de sauts)."""
        return len(chemin) - 1

    # ── Déplacements simples (aucune capture disponible) ────────────────────
    def _tous_deplacements_simples(self, couleur: int) -> List[Tuple[Pion, Chemin]]:
        res = []
        for p in self.pions[couleur]:
            if p.est_dame:
                res.extend(self._deplacements_dame(p))
            else:
                res.extend(self._deplacements_pion(p))
        return res

    def _deplacements_pion(self, p: Pion) -> List[Tuple[Pion, Chemin]]:
        """Pion simple : avance uniquement dans sa direction."""
        fwd = -1 if p.couleur == BLANC else 1
        res = []
        for dc in (-1, 1):
            nl, nc = p.ligne + fwd, p.col + dc
            if 0 <= nl < N and 0 <= nc < N and self.grille[nl][nc] == VIDE:
                res.append((p, [(p.ligne, p.col), (nl, nc)]))
        return res

    def _deplacements_dame(self, p: Pion) -> List[Tuple[Pion, Chemin]]:
        """
        Dame à vol libre : se déplace sur toute une diagonale,
        case par case, jusqu'à rencontrer un obstacle ou le bord.
        """
        res = []
        for dl, dc in ((-1,-1),(-1,1),(1,-1),(1,1)):
            nl, nc = p.ligne + dl, p.col + dc
            while 0 <= nl < N and 0 <= nc < N:
                if self.grille[nl][nc] != VIDE:
                    break
                res.append((p, [(p.ligne, p.col), (nl, nc)]))
                nl += dl
                nc += dc
        return res

    # ── Captures ────────────────────────────────────────────────────────────
    def _toutes_captures(self, couleur: int) -> List[Tuple[Pion, Chemin]]:
        res = []
        for p in self.pions[couleur]:
            seqs = self._captures_rec(p, p.ligne, p.col,
                                      frozenset(), deepcopy(self.grille),
                                      p.est_dame)
            for s in seqs:
                res.append((p, s))
        return res

    def _captures_rec(self, pion: Pion, l: int, c: int,
                       deja_cap: frozenset, g: List[List[int]],
                       est_dame: bool) -> List[Chemin]:
        """
        Génère toutes les séquences de capture possibles depuis (l, c).

        Règles FMJD appliquées :
        - Pions ET dames peuvent capturer dans les 4 directions
        - Dames : vol libre avant ET après la pièce sautée
        - Pion promu EN COURS de rafle : continue comme pion jusqu'à la fin
          (la promotion n'est effective qu'après la rafle complète)
        - Un pion capturé est retiré de la grille, mais ne peut être
          re-capturé dans la même rafle
        """
        adverse = NOIR if pion.couleur == BLANC else BLANC
        res = []

        if est_dame:
            # ── Capture à vol libre (dame) ──────────────────────────────
            for dl, dc in ((-1,-1),(-1,1),(1,-1),(1,1)):
                # Chercher une pièce adverse sur cette diagonale
                nl, nc = l + dl, c + dc
                while 0 <= nl < N and 0 <= nc < N:
                    case = g[nl][nc]
                    est_adv = (case == adverse
                               or (adverse == NOIR  and case == DAME_N)
                               or (adverse == BLANC and case == DAME_B))
                    if est_adv and (nl, nc) not in deja_cap:
                        # Chercher toutes les cases d'atterrissage
                        al, ac = nl + dl, nc + dc
                        while 0 <= al < N and 0 <= ac < N and g[al][ac] == VIDE:
                            g2 = deepcopy(g)
                            g2[nl][nc] = VIDE
                            g2[l][c]   = VIDE
                            g2[al][ac] = pion.code_grille()
                            suite = self._captures_rec(
                                pion, al, ac, deja_cap | {(nl, nc)}, g2, True)
                            if suite:
                                for s in suite:
                                    res.append([(l, c)] + s)
                            else:
                                res.append([(l, c), (al, ac)])
                            al += dl
                            ac += dc
                        break  # La pièce adverse bloque la diagonale
                    elif case != VIDE:
                        break  # Case occupée par une pièce alliée
                    nl += dl
                    nc += dc
        else:
            # ── Capture pion simple (4 directions, saut de 1) ──────────
            for dl, dc in ((-1,-1),(-1,1),(1,-1),(1,1)):
                ml, mc = l + dl, c + dc      # case à sauter
                al, ac = l + 2*dl, c + 2*dc  # case d'arrivée
                if not (0 <= ml < N and 0 <= mc < N
                        and 0 <= al < N and 0 <= ac < N):
                    continue
                case_m = g[ml][mc]
                est_adv = (case_m == adverse
                           or (adverse == NOIR  and case_m == DAME_N)
                           or (adverse == BLANC and case_m == DAME_B))
                if est_adv and g[al][ac] == VIDE and (ml, mc) not in deja_cap:
                    g2 = deepcopy(g)
                    g2[ml][mc] = VIDE
                    g2[l][c]   = VIDE
                    g2[al][ac] = pion.code_grille()

                    # Règle FMJD : la promotion en cours de rafle n'active
                    # PAS le vol libre — le pion reste "pion" pour la suite.
                    # (Il sera promu après la rafle complète dans appliquer().)
                    suite = self._captures_rec(
                        pion, al, ac, deja_cap | {(ml, mc)}, g2, False)
                    if suite:
                        for s in suite:
                            res.append([(l, c)] + s)
                    else:
                        res.append([(l, c), (al, ac)])
        return res

    # ── Application d'un mouvement ──────────────────────────────────────────
    def appliquer(self, pion: Pion, chemin: Chemin) -> List[Pion]:
        """
        Joue le mouvement. Retourne les pions capturés.
        La promotion est appliquée APRÈS la rafle complète.
        """
        captures: List[Pion] = []

        if pion.est_dame:
            # ── Déplacement / capture dame (vol libre) ──────────────────
            for i in range(len(chemin) - 1):
                l1, c1 = chemin[i]
                l2, c2 = chemin[i + 1]
                dl = (1 if l2 > l1 else -1)
                dc = (1 if c2 > c1 else -1)
                # Effacer le chemin intermédiaire + capturer éventuellement
                nl, nc = l1 + dl, c1 + dc
                while (nl, nc) != (l2, c2):
                    v = self.grille[nl][nc]
                    if v != VIDE:
                        cap = self.pion_en(nl, nc)
                        if cap and cap not in captures:
                            captures.append(cap)
                            self.pions[cap.couleur].remove(cap)
                            self.grille[nl][nc] = VIDE
                    nl += dl
                    nc += dc
            self.grille[pion.ligne][pion.col] = VIDE
            pion.ligne, pion.col = chemin[-1]
            self.grille[pion.ligne][pion.col] = pion.code_grille()

        else:
            # ── Déplacement / capture pion simple ───────────────────────
            for i in range(len(chemin) - 1):
                l1, c1 = chemin[i]
                l2, c2 = chemin[i + 1]
                if abs(l2 - l1) == 2:
                    ml, mc = (l1 + l2) // 2, (c1 + c2) // 2
                    cap = self.pion_en(ml, mc)
                    if cap:
                        captures.append(cap)
                        self.pions[cap.couleur].remove(cap)
                        self.grille[ml][mc] = VIDE

            self.grille[pion.ligne][pion.col] = VIDE
            pion.ligne, pion.col = chemin[-1]

            # Promotion APRÈS la rafle complète (règle FMJD)
            if pion.couleur == BLANC and pion.ligne == 0:
                pion.est_dame = True
            elif pion.couleur == NOIR and pion.ligne == N - 1:
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

    # ── Copie ───────────────────────────────────────────────────────────────
    def copie(self) -> "Plateau":
        p = Plateau.__new__(Plateau)
        p.grille = deepcopy(self.grille)
        p.pions = {
            BLANC: [deepcopy(x) for x in self.pions[BLANC]],
            NOIR:  [deepcopy(x) for x in self.pions[NOIR]],
        }
        return p

    def cle(self) -> str:
        """Clé compacte pour la table Q."""
        parts = []
        for l in range(N):
            for c in range(N):
                v = self.grille[l][c]
                if v:
                    parts.append(f"{l}{c}{v}")
        return "|".join(parts)
