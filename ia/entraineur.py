"""
ia/entraineur.py
----------------
Fait jouer deux agents l'un contre l'autre en boucle (self-play).
Utilise depuis le controleur dans un thread separe pour ne pas
bloquer l'interface pendant l'entrainement.
"""

from __future__ import annotations
from model.plateau import Plateau, BLANC, NOIR
from ia.agent_ql import AgentQL
from typing import Callable

# nombre max de coups par partie, pour eviter les boucles infinies
MAX_COUPS = 150


class Entraineur:

    def __init__(self,
                 agent_blanc: AgentQL,
                 agent_noir:  AgentQL,
                 on_fin_partie: Callable | None = None):
        """
        on_fin_partie(n_partie, resultat) : callback appele apres chaque partie,
        utile pour mettre a jour la barre de progression dans la vue.
        """
        self.blanc         = agent_blanc
        self.noir          = agent_noir
        self.on_fin_partie = on_fin_partie

    def jouer_une_partie(self):
        plateau = Plateau()
        courant = BLANC
        n_coups = 0
        pts     = {BLANC: 0.0, NOIR: 0.0}

        while n_coups < MAX_COUPS:
            fin = plateau.gagnant()
            if fin:
                break

            agent = self.blanc if courant == BLANC else self.noir
            choix = agent.choisir(plateau)

            if not choix:
                fin = NOIR if courant == BLANC else BLANC
                break

            pion, chemin = choix
            p_reel = plateau.pion_en(pion.ligne, pion.col)
            if p_reel is None:
                courant = NOIR if courant == BLANC else BLANC
                continue

            captures = plateau.appliquer(p_reel, chemin)
            pts[courant] += sum(c.valeur for c in captures)
            agent.apprendre(plateau, captures, p_reel)
            courant = NOIR if courant == BLANC else BLANC
            n_coups += 1

        gagnant = plateau.gagnant()
        # si la limite de coups est atteinte, le joueur avec le plus de points gagne
        if gagnant == 0:
            gagnant = BLANC if pts[BLANC] >= pts[NOIR] else NOIR

        self.blanc.fin_partie(gagnant)
        self.noir.fin_partie(gagnant)

        return {
            "gagnant"   : gagnant,
            "pts_blanc" : pts[BLANC],
            "pts_noir"  : pts[NOIR],
            "coups"     : n_coups,
        }

    def entrainer(self, n):
        for i in range(n):
            res = self.jouer_une_partie()
            if self.on_fin_partie:
                self.on_fin_partie(i + 1, res)
        self.blanc.sauvegarder()
        self.noir.sauvegarder()
