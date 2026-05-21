"""
IA - agent_ql.py
Agent IA utilisant le Q-Learning (apprentissage par renforcement).

Concept :
- L'IA apprend en jouant plusieurs parties contre elle-même.
- Elle maintient une table Q : Q[état][action] = valeur estimée
- Récompenses : +1 par pion capturé, +3 par dame capturée, +10 victoire, -10 défaite
- Stratégie epsilon-greedy : explore aléatoirement au début, puis exploite ce qu'elle a appris.

Objectif : MAXIMISER LES POINTS (1 pion = 1 point, 1 dame = 3 points).
"""

import random
import json
import os
from copy import deepcopy
from model.plateau import Plateau, BLANC, NOIR, TAILLE


class AgentQL:
    """
    Agent Q-Learning pour le jeu de dames.
    
    Table Q : dictionnaire {etat_str: {action_str: valeur}}
    Un état est une représentation compacte du plateau.
    Une action est le chemin d'un mouvement.
    """

    # Hyperparamètres d'apprentissage
    ALPHA = 0.1       # Taux d'apprentissage : quel poids donner aux nouvelles infos
    GAMMA = 0.9       # Facteur de discount : importance des récompenses futures
    EPSILON_INIT = 1.0   # Exploration initiale (100% aléatoire)
    EPSILON_MIN = 0.05   # Exploration minimale (5% aléatoire)
    EPSILON_DECAY = 0.995  # Décroissance de l'exploration par partie

    # Récompenses
    RECOMPENSE_PION_CAPTURE = 1      # +1 par pion ennemi capturé
    RECOMPENSE_DAME_CAPTURE = 3      # +3 par dame ennemie capturée
    RECOMPENSE_VICTOIRE = 10         # +10 pour gagner la partie
    RECOMPENSE_DEFAITE = -10         # -10 pour perdre
    RECOMPENSE_PROMOTION = 2         # +2 pour promouvoir un pion en dame
    RECOMPENSE_NEUTRE = 0            # Mouvement sans événement

    def __init__(self, couleur: int, fichier_q: str = None):
        """
        Initialise l'agent.
        couleur : BLANC ou NOIR
        fichier_q : chemin du fichier de sauvegarde de la table Q
        """
        self.couleur = couleur
        self.adverse = NOIR if couleur == BLANC else BLANC
        self.table_q = {}           # Table Q
        self.epsilon = self.EPSILON_INIT
        self.parties_jouees = 0
        self.historique_scores = []  # Score (points) par partie
        self.historique_victoires = []  # 1=victoire, 0=défaite, 0.5=nul
        self.total_points_gagnes = 0

        self.fichier_q = fichier_q
        if fichier_q and os.path.exists(fichier_q):
            self.charger(fichier_q)

        # Mémorisation pour l'apprentissage
        self._dernier_etat = None
        self._derniere_action = None

    def etat_vers_cle(self, plateau: Plateau) -> str:
        """
        Encode l'état du plateau en une chaîne compacte.
        On encode seulement les cases non vides pour économiser la mémoire.
        """
        cle = []
        for i in range(TAILLE):
            for j in range(TAILLE):
                if plateau.grille[i][j] != 0:
                    cle.append(f"{i}{j}{plateau.grille[i][j]}")
        return "|".join(cle)

    def action_vers_cle(self, chemin: list) -> str:
        """Encode un mouvement (chemin) en chaîne."""
        return "_".join(f"{l}{c}" for l, c in chemin)

    def obtenir_q(self, etat_cle: str, action_cle: str) -> float:
        """Retourne la valeur Q pour un couple état-action (0.0 par défaut)."""
        return self.table_q.get(etat_cle, {}).get(action_cle, 0.0)

    def mettre_a_jour_q(self, etat_cle: str, action_cle: str,
                         recompense: float, prochain_etat_cle: str,
                         prochaines_actions_cles: list):
        """
        Mise à jour de la table Q selon la formule de Bellman :
        Q(s,a) ← Q(s,a) + α * [r + γ * max Q(s',a') - Q(s,a)]
        """
        q_actuel = self.obtenir_q(etat_cle, action_cle)

        if prochaines_actions_cles:
            q_max_suivant = max(
                self.obtenir_q(prochain_etat_cle, a)
                for a in prochaines_actions_cles
            )
        else:
            q_max_suivant = 0.0

        nouveau_q = q_actuel + self.ALPHA * (
            recompense + self.GAMMA * q_max_suivant - q_actuel
        )

        if etat_cle not in self.table_q:
            self.table_q[etat_cle] = {}
        self.table_q[etat_cle][action_cle] = nouveau_q

    def choisir_action(self, plateau: Plateau) -> tuple:
        """
        Choisit un mouvement selon la stratégie epsilon-greedy :
        - Avec probabilité epsilon : mouvement aléatoire (exploration)
        - Sinon : meilleur mouvement connu (exploitation)
        
        Retourne (pion, chemin) ou None si aucun mouvement possible.
        """
        mouvements = plateau.mouvements_possibles(self.couleur)
        if not mouvements:
            return None

        etat_cle = self.etat_vers_cle(plateau)

        if random.random() < self.epsilon:
            # Exploration : mouvement aléatoire
            choix = random.choice(mouvements)
        else:
            # Exploitation : meilleur mouvement selon Q
            meilleure_valeur = float('-inf')
            meilleur = mouvements[0]
            for pion, chemin in mouvements:
                action_cle = self.action_vers_cle(chemin)
                val = self.obtenir_q(etat_cle, action_cle)
                if val > meilleure_valeur:
                    meilleure_valeur = val
                    meilleur = (pion, chemin)
            choix = meilleur

        # Mémoriser pour la mise à jour Q
        self._dernier_etat = etat_cle
        self._derniere_action = self.action_vers_cle(choix[1])

        return choix

    def apprendre(self, plateau_apres: Plateau, recompense: float):
        """
        Met à jour la table Q après avoir effectué un mouvement.
        Appelé après chaque coup de l'IA.
        """
        if self._dernier_etat is None or self._derniere_action is None:
            return

        prochain_etat_cle = self.etat_vers_cle(plateau_apres)
        prochains_mouvements = plateau_apres.mouvements_possibles(self.couleur)
        prochaines_actions_cles = [
            self.action_vers_cle(chemin)
            for _, chemin in prochains_mouvements
        ]

        self.mettre_a_jour_q(
            self._dernier_etat,
            self._derniere_action,
            recompense,
            prochain_etat_cle,
            prochaines_actions_cles
        )

    def fin_de_partie(self, gagnant: int, points_gagnes: int):
        """
        Appelé à la fin d'une partie pour :
        - Appliquer la récompense terminale
        - Décrémenter epsilon
        - Mettre à jour les statistiques
        """
        if gagnant == self.couleur:
            recompense_finale = self.RECOMPENSE_VICTOIRE
            self.historique_victoires.append(1)
        elif gagnant == self.adverse:
            recompense_finale = self.RECOMPENSE_DEFAITE
            self.historique_victoires.append(0)
        else:
            recompense_finale = 0
            self.historique_victoires.append(0.5)

        # Mise à jour Q terminale (pas d'état suivant)
        if self._dernier_etat and self._derniere_action:
            if self._dernier_etat not in self.table_q:
                self.table_q[self._dernier_etat] = {}
            q = self.obtenir_q(self._dernier_etat, self._derniere_action)
            self.table_q[self._dernier_etat][self._derniere_action] = (
                q + self.ALPHA * (recompense_finale - q)
            )

        self.parties_jouees += 1
        self.historique_scores.append(points_gagnes)
        self.total_points_gagnes += points_gagnes

        # Décroissance epsilon
        self.epsilon = max(
            self.EPSILON_MIN,
            self.epsilon * self.EPSILON_DECAY
        )

        # Reset mémorisation
        self._dernier_etat = None
        self._derniere_action = None

    def stats(self) -> dict:
        """Retourne les statistiques d'apprentissage."""
        n = self.parties_jouees
        victoires = sum(1 for v in self.historique_victoires if v == 1)
        return {
            "parties": n,
            "victoires": victoires,
            "taux_victoire": round(victoires / n * 100, 1) if n > 0 else 0,
            "score_moyen": round(sum(self.historique_scores[-50:]) /
                                  min(50, len(self.historique_scores)), 2)
                           if self.historique_scores else 0,
            "epsilon": round(self.epsilon, 3),
            "etats_connus": len(self.table_q),
        }

    def sauvegarder(self, chemin: str):
        """Sauvegarde la table Q et les paramètres."""
        data = {
            "table_q": self.table_q,
            "epsilon": self.epsilon,
            "parties_jouees": self.parties_jouees,
            "historique_scores": self.historique_scores[-200:],
            "historique_victoires": self.historique_victoires[-200:],
        }
        with open(chemin, 'w') as f:
            json.dump(data, f)

    def charger(self, chemin: str):
        """Charge une table Q sauvegardée."""
        try:
            with open(chemin, 'r') as f:
                data = json.load(f)
            self.table_q = data.get("table_q", {})
            self.epsilon = data.get("epsilon", self.EPSILON_INIT)
            self.parties_jouees = data.get("parties_jouees", 0)
            self.historique_scores = data.get("historique_scores", [])
            self.historique_victoires = data.get("historique_victoires", [])
            print(f"[IA] Table Q chargée : {len(self.table_q)} états connus, "
                  f"{self.parties_jouees} parties jouées")
        except Exception as e:
            print(f"[IA] Impossible de charger : {e}")
