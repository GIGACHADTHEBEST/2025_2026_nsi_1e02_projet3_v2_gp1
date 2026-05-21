"""
MODEL - Plateau.py
Représente l'état du plateau de jeu de dames.
Structure MVC : le modèle ne connaît pas la vue ni le contrôleur.
"""

from copy import deepcopy

VIDE = 0
BLANC = 1
NOIR = 2
DAME_BLANC = 3
DAME_NOIR = 4

TAILLE = 8  # Plateau 8x8


class Pion:
    """Représente un pion sur le plateau."""

    def __init__(self, couleur: int, ligne: int, col: int):
        self.couleur = couleur  # BLANC ou NOIR
        self.est_dame = False
        self.ligne = ligne
        self.col = col

    def valeur(self) -> int:
        """Retourne la valeur du pion : 1 pion normal, 3 pour une dame."""
        return 3 if self.est_dame else 1

    def __repr__(self):
        nom = "Dame" if self.est_dame else "Pion"
        c = "Blanc" if self.couleur == BLANC else "Noir"
        return f"{nom} {c} ({self.ligne},{self.col})"


class Plateau:
    """
    Représente le plateau de jeu de dames (8x8).
    Contient la logique du jeu : mouvements, captures, fin de partie.
    """

    def __init__(self):
        self.grille = [[VIDE] * TAILLE for _ in range(TAILLE)]
        self.pions = {BLANC: [], NOIR: []}
        self.initialiser()

    def initialiser(self):
        """Place les pions en position initiale."""
        self.grille = [[VIDE] * TAILLE for _ in range(TAILLE)]
        self.pions = {BLANC: [], NOIR: []}

        # Pions noirs : lignes 0, 1, 2
        for ligne in range(3):
            for col in range(TAILLE):
                if (ligne + col) % 2 == 1:
                    p = Pion(NOIR, ligne, col)
                    self.pions[NOIR].append(p)
                    self.grille[ligne][col] = NOIR

        # Pions blancs : lignes 5, 6, 7
        for ligne in range(5, TAILLE):
            for col in range(TAILLE):
                if (ligne + col) % 2 == 1:
                    p = Pion(BLANC, ligne, col)
                    self.pions[BLANC].append(p)
                    self.grille[ligne][col] = BLANC

    def get_pion(self, ligne: int, col: int):
        """Retourne le pion à une position donnée, ou None."""
        for couleur in [BLANC, NOIR]:
            for p in self.pions[couleur]:
                if p.ligne == ligne and p.col == col:
                    return p
        return None

    def score(self, couleur: int) -> int:
        """Calcule le score : 1 point par pion, 3 points par dame."""
        return sum(p.valeur() for p in self.pions[couleur])

    def mouvements_possibles(self, couleur: int) -> list:
        """
        Retourne tous les mouvements possibles pour une couleur.
        Les captures sont prioritaires sur les déplacements simples.
        Retourne une liste de (pion, [(l1,c1), (l2,c2), ...]) représentant
        le chemin complet (y compris captures multiples).
        """
        captures = self._toutes_captures(couleur)
        if captures:
            return captures
        return self._tous_deplacements(couleur)

    def _tous_deplacements(self, couleur: int) -> list:
        """Retourne tous les déplacements simples (sans capture)."""
        result = []
        direction = -1 if couleur == BLANC else 1
        for p in self.pions[couleur]:
            if p.est_dame:
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            else:
                directions = [(direction, -1), (direction, 1)]

            for dl, dc in directions:
                nl, nc = p.ligne + dl, p.col + dc
                if 0 <= nl < TAILLE and 0 <= nc < TAILLE:
                    if self.grille[nl][nc] == VIDE:
                        result.append((p, [(p.ligne, p.col), (nl, nc)]))
        return result

    def _toutes_captures(self, couleur: int) -> list:
        """Retourne toutes les séquences de captures possibles."""
        result = []
        for p in self.pions[couleur]:
            sequences = self._captures_depuis(p, p.ligne, p.col,
                                               set(), deepcopy(self.grille))
            for seq in sequences:
                result.append((p, seq))
        return result

    def _captures_depuis(self, pion, ligne: int, col: int,
                         captures_faites: set, grille_temp) -> list:
        """Trouve toutes les séquences de captures possibles depuis une position."""
        couleur = pion.couleur
        adverse = NOIR if couleur == BLANC else BLANC
        direction = -1 if couleur == BLANC else 1

        if pion.est_dame:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            directions = [(direction, -1), (direction, 1),
                          (-direction, -1), (-direction, 1)]

        sequences_trouvees = []
        for dl, dc in directions:
            ml, mc = ligne + dl, col + dc    # case du pion à capturer
            al, ac = ligne + 2*dl, col + 2*dc  # case d'atterrissage

            if not (0 <= ml < TAILLE and 0 <= mc < TAILLE):
                continue
            if not (0 <= al < TAILLE and 0 <= ac < TAILLE):
                continue

            case_milieu = grille_temp[ml][mc]
            est_adverse = case_milieu in [adverse,
                                           DAME_NOIR if adverse == NOIR else DAME_BLANC,
                                           DAME_BLANC if adverse == BLANC else DAME_NOIR]
            # Simplifié : on vérifie juste si la couleur correspond
            est_adverse = (case_milieu == adverse or
                           (adverse == NOIR and case_milieu == DAME_NOIR) or
                           (adverse == BLANC and case_milieu == DAME_BLANC))

            if est_adverse and grille_temp[al][ac] == VIDE:
                cle = (ml, mc)
                if cle not in captures_faites:
                    # On simule la capture
                    new_grille = deepcopy(grille_temp)
                    new_grille[ml][mc] = VIDE
                    new_grille[ligne][col] = VIDE
                    new_grille[al][ac] = (DAME_BLANC if pion.est_dame and couleur == BLANC
                                          else DAME_NOIR if pion.est_dame and couleur == NOIR
                                          else couleur)

                    new_captures = captures_faites | {cle}
                    suite = self._captures_depuis(pion, al, ac,
                                                  new_captures, new_grille)
                    if suite:
                        for s in suite:
                            sequences_trouvees.append([(ligne, col)] + s)
                    else:
                        sequences_trouvees.append([(ligne, col), (al, ac)])

        return sequences_trouvees

    def appliquer_mouvement(self, pion, chemin: list) -> list:
        """
        Applique un mouvement au plateau.
        Retourne la liste des pions capturés (pour scoring IA).
        """
        captures = []
        depart = chemin[0]
        arrivee = chemin[-1]

        # Trouver les pions capturés
        for i in range(len(chemin) - 1):
            l1, c1 = chemin[i]
            l2, c2 = chemin[i + 1]
            ml = (l1 + l2) // 2
            mc = (c1 + c2) // 2
            if abs(l2 - l1) == 2:  # C'est une capture
                p_capturé = self.get_pion(ml, mc)
                if p_capturé:
                    captures.append(p_capturé)
                    self.pions[p_capturé.couleur].remove(p_capturé)
                    self.grille[ml][mc] = VIDE

        # Déplacer le pion
        self.grille[depart[0]][depart[1]] = VIDE
        pion.ligne, pion.col = arrivee

        # Promotion en dame
        if pion.couleur == BLANC and arrivee[0] == 0 and not pion.est_dame:
            pion.est_dame = True
            self.grille[arrivee[0]][arrivee[1]] = DAME_BLANC
        elif pion.couleur == NOIR and arrivee[0] == TAILLE - 1 and not pion.est_dame:
            pion.est_dame = True
            self.grille[arrivee[0]][arrivee[1]] = DAME_NOIR
        else:
            self.grille[arrivee[0]][arrivee[1]] = (
                DAME_BLANC if pion.est_dame and pion.couleur == BLANC else
                DAME_NOIR if pion.est_dame and pion.couleur == NOIR else
                pion.couleur
            )

        return captures

    def partie_terminee(self) -> int:
        """
        Vérifie si la partie est terminée.
        Retourne BLANC, NOIR, ou 0 si la partie continue.
        """
        if not self.pions[BLANC] or not self.mouvements_possibles(BLANC):
            return NOIR
        if not self.pions[NOIR] or not self.mouvements_possibles(NOIR):
            return BLANC
        return 0

    def copie(self):
        """Retourne une copie profonde du plateau (pour la simulation IA)."""
        nouveau = Plateau.__new__(Plateau)
        nouveau.grille = deepcopy(self.grille)
        nouveau.pions = {
            BLANC: [deepcopy(p) for p in self.pions[BLANC]],
            NOIR: [deepcopy(p) for p in self.pions[NOIR]]
        }
        return nouveau

    def __repr__(self):
        lignes = []
        for i, ligne in enumerate(self.grille):
            lignes.append(f"{i} {ligne}")
        return "\n".join(lignes)
