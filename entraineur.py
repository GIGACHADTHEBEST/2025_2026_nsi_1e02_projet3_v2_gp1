"""
IA - entraineur.py
Gère l'entraînement de l'IA par auto-jeu (self-play).
L'IA Noire joue contre l'IA Blanche, les deux apprennent.
"""

from model.plateau import Plateau, BLANC, NOIR
from ia.agent_ql import AgentQL
import time


class Entraineur:
    """
    Fait jouer deux agents IA l'un contre l'autre pour s'entraîner.
    Les deux agents apprennent simultanément.
    """

    MAX_COUPS = 200  # Limite de coups par partie pour éviter les boucles infinies

    def __init__(self, agent_blanc: AgentQL, agent_noir: AgentQL,
                 callback_progression=None):
        """
        agent_blanc : IA jouant les blancs
        agent_noir : IA jouant les noirs
        callback_progression : fonction(n_partie, stats) appelée après chaque partie
        """
        self.agent_blanc = agent_blanc
        self.agent_noir = agent_noir
        self.callback = callback_progression

    def jouer_partie(self) -> dict:
        """
        Fait jouer une partie complète entre les deux agents.
        Retourne les résultats de la partie.
        """
        plateau = Plateau()
        joueur_courant = BLANC
        n_coups = 0
        points_blanc = 0
        points_noir = 0

        while n_coups < self.MAX_COUPS:
            gagnant = plateau.partie_terminee()
            if gagnant != 0:
                break

            agent = (self.agent_blanc if joueur_courant == BLANC
                     else self.agent_noir)

            # Choisir l'action
            choix = agent.choisir_action(plateau)
            if choix is None:
                gagnant = NOIR if joueur_courant == BLANC else BLANC
                break

            pion, chemin = choix

            # Compter les points avant
            score_avant = plateau.score(joueur_courant)

            # Appliquer le mouvement
            captures = plateau.appliquer_mouvement(pion, chemin)

            # Calculer la récompense
            recompense = 0
            for cap in captures:
                recompense += cap.valeur()  # 1 par pion, 3 par dame

            # Vérifier promotion
            if pion.est_dame and len(chemin) <= 2:
                recompense += AgentQL.RECOMPENSE_PROMOTION

            # Accumuler les points
            if joueur_courant == BLANC:
                points_blanc += len(captures)
            else:
                points_noir += len(captures)

            # Apprendre de ce coup
            agent.apprendre(plateau, recompense)

            joueur_courant = NOIR if joueur_courant == BLANC else BLANC
            n_coups += 1

        # Fin de partie
        gagnant = plateau.partie_terminee()
        if gagnant == 0:
            # Partie nulle (trop de coups)
            gagnant = BLANC if points_blanc >= points_noir else NOIR

        self.agent_blanc.fin_de_partie(gagnant, points_blanc)
        self.agent_noir.fin_de_partie(gagnant, points_noir)

        return {
            "gagnant": gagnant,
            "n_coups": n_coups,
            "points_blanc": points_blanc,
            "points_noir": points_noir,
        }

    def entrainer(self, n_parties: int, sauvegarder_tous: int = 100):
        """
        Lance n_parties d'entraînement.
        Sauvegarde toutes les 'sauvegarder_tous' parties.
        """
        debut = time.time()
        for i in range(n_parties):
            result = self.jouer_partie()
            if self.callback:
                self.callback(i + 1, result,
                               self.agent_blanc.stats(),
                               self.agent_noir.stats())

            if (i + 1) % sauvegarder_tous == 0:
                if self.agent_blanc.fichier_q:
                    self.agent_blanc.sauvegarder(self.agent_blanc.fichier_q)
                if self.agent_noir.fichier_q:
                    self.agent_noir.sauvegarder(self.agent_noir.fichier_q)

        duree = time.time() - debut
        print(f"[Entraînement] {n_parties} parties en {duree:.1f}s "
              f"({n_parties/duree:.0f} parties/s)")
