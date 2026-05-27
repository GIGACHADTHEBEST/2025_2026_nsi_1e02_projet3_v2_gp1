"""
ia/agent_ql.py
--------------
Agent Q-Learning pour le jeu de dames.

On a essaye plusieurs configurations avant de fixer ces hyperparametres :
un alpha trop faible (genre 0.05) donnait une convergence tres lente,
et un epsilon_decay trop agressif faisait que l'agent arretait
d'explorer beaucoup trop tot.

Techniques utilisees :
  - alpha eleve (0.3) : apprend vite des nouvelles experiences
  - epsilon decay rapide (0.98/partie) : exploite rapidement ce qu'il sait
  - recompenses a chaque coup (pas seulement en fin de partie)
  - reward shaping : petit bonus quand un pion avance vers la promotion
  - experience replay leger : les N dernieres transitions sont rejouees
  - heuristique d'init : si un etat est inconnu, on estime Q au lieu de 0

Objectif : 1 pion = 1 point, maximiser les points captures.
"""

from __future__ import annotations
import random
import json
import os
from collections import deque
from model.plateau import Plateau, BLANC, NOIR, VALEUR_PION, VALEUR_DAME, N

# hyperparametres
ALPHA        = 0.30
GAMMA        = 0.92
EPS_INIT     = 0.90
EPS_MIN      = 0.05
EPS_DECAY    = 0.980
REPLAY_SIZE  = 2000
REPLAY_BATCH = 32

# valeurs de recompense
R_PION   = 1.0
R_DAME   = 3.0
R_PROMO  = 2.5
R_WIN    = 10.0
R_LOSE   = -10.0
R_AVANCE = 0.05   # petit bonus par rangee gagnee


class AgentQL:
    """
    Agent Q-Learning avec reward shaping et experience replay.
    En pratique il commence a jouer decemment autour de 200-500 parties.
    """

    def __init__(self, couleur, chemin_save=None):
        self.couleur     = couleur
        self.adverse     = NOIR if couleur == BLANC else BLANC
        self.chemin_save = chemin_save

        # table Q : {cle_etat: {cle_action: valeur}}
        self.Q = {}

        self.epsilon          = EPS_INIT
        self.nb_parties       = 0
        self.scores           = []   # points captures par partie
        self.victoires        = []   # 1 si gagne, 0 sinon
        self.pts_cette_partie = 0.0

        # buffer pour l'experience replay
        self._replay = deque(maxlen=REPLAY_SIZE)

        # memorisation du dernier pas (necessaire pour la mise a jour Q)
        self._s       = None
        self._a       = None
        self._l_avant = 0

        if chemin_save and os.path.exists(chemin_save):
            self._charger()

    # table Q : lecture/ecriture
    def _q(self, s, a):
        return self.Q.get(s, {}).get(a, 0.0)

    def _set_q(self, s, a, v):
        if s not in self.Q:
            self.Q[s] = {}
        self.Q[s][a] = v

    # encodage d'un chemin en cle lisible
    @staticmethod
    def _cle_action(chemin):
        return "_".join(f"{l}{c}" for l, c in chemin)

    # estimation de la qualite d'un etat quand il est inconnu de la table Q
    def _heuristique(self, plateau):
        sc    = plateau.score(self.couleur) - plateau.score(self.adverse)
        bonus = 0.0
        for p in plateau.pions[self.couleur]:
            rang   = (N - 1 - p.ligne) if self.couleur == BLANC else p.ligne
            bonus += rang * 0.015
        return sc + bonus

    # -----------------------------------------------------------------------
    # Choisir une action (epsilon-greedy)
    # -----------------------------------------------------------------------
    def choisir(self, plateau):
        """Retourne (pion, chemin) ou None si aucun mouvement possible."""
        mvs = plateau.mouvements_legaux(self.couleur)
        if not mvs:
            return None

        s = plateau.cle()

        if random.random() < self.epsilon:
            choix = random.choice(mvs)
        else:
            best_v = float("-inf")
            best   = mvs[0]
            for pion, chemin in mvs:
                a = self._cle_action(chemin)
                v = self._q(s, a)
                # etat inconnu : on estime via heuristique plutot que 0
                if v == 0.0 and s not in self.Q:
                    sim = plateau.copie()
                    sim.appliquer(
                        sim.pion_en(pion.ligne, pion.col) or pion, chemin)
                    v = self._heuristique(sim) * 0.1
                if v > best_v:
                    best_v = v
                    best   = (pion, chemin)
            choix = best

        self._s       = s
        self._a       = self._cle_action(choix[1])
        self._l_avant = choix[0].ligne
        return choix

    # -----------------------------------------------------------------------
    # Mise a jour apres un coup
    # -----------------------------------------------------------------------
    def apprendre(self, plateau_apres, captures, pion_joue):
        """Appelé par le controleur apres chaque coup joue."""
        if self._s is None:
            return

        # recompense immediate
        r = 0.0
        for cap in captures:
            r += R_DAME if cap.est_dame else R_PION

        # bonus de promotion (seulement si le pion vient d'etre promu)
        if pion_joue.est_dame:
            l_promo = 0 if self.couleur == BLANC else N - 1
            if pion_joue.ligne == l_promo:
                r += R_PROMO

        # reward shaping : avancer vaut un tout petit peu
        l_apres = pion_joue.ligne
        if self.couleur == BLANC:
            r += R_AVANCE * max(0, self._l_avant - l_apres)
        else:
            r += R_AVANCE * max(0, l_apres - self._l_avant)

        self.pts_cette_partie += sum(
            (R_DAME if cap.est_dame else R_PION) for cap in captures
        )

        s2   = plateau_apres.cle()
        mvs2 = plateau_apres.mouvements_legaux(self.couleur)
        done = len(mvs2) == 0

        self._replay.append((self._s, self._a, r, s2,
                              [self._cle_action(ch) for _, ch in mvs2], done))

        # mise a jour directe (TD)
        self._td_update(self._s, self._a, r, s2,
                        [self._cle_action(ch) for _, ch in mvs2])

        # experience replay
        if len(self._replay) >= REPLAY_BATCH:
            self._experience_replay()

        self._s = None
        self._a = None

    def _td_update(self, s, a, r, s2, actions2):
        q_now = self._q(s, a)
        q_max = max((self._q(s2, a2) for a2 in actions2), default=0.0)
        self._set_q(s, a, q_now + ALPHA * (r + GAMMA * q_max - q_now))

    def _experience_replay(self):
        batch = random.sample(self._replay, REPLAY_BATCH)
        for s, a, r, s2, actions2, done in batch:
            q_max = 0.0 if done else max(
                (self._q(s2, a2) for a2 in actions2), default=0.0)
            q_now = self._q(s, a)
            self._set_q(s, a, q_now + ALPHA * (r + GAMMA * q_max - q_now))

    # -----------------------------------------------------------------------
    # Fin de partie
    # -----------------------------------------------------------------------
    def fin_partie(self, gagnant):
        r_fin = R_WIN if gagnant == self.couleur else (
                R_LOSE if gagnant == self.adverse else 0.0)
        if self._s and self._a:
            q = self._q(self._s, self._a)
            self._set_q(self._s, self._a, q + ALPHA * (r_fin - q))

        self.nb_parties += 1
        self.victoires.append(1 if gagnant == self.couleur else 0)
        self.scores.append(self.pts_cette_partie)
        self.pts_cette_partie = 0.0

        self.epsilon = max(EPS_MIN, self.epsilon * EPS_DECAY)
        self._s = None
        self._a = None

    # -----------------------------------------------------------------------
    # Stats
    # -----------------------------------------------------------------------
    def stats(self):
        v50 = self.victoires[-50:]
        s50 = self.scores[-50:]
        return {
            "parties"       : self.nb_parties,
            "taux_victoire" : round(sum(v50) / max(1, len(v50)) * 100, 1),
            "score_moyen"   : round(sum(s50) / max(1, len(s50)), 2),
            "epsilon"       : round(self.epsilon, 3),
            "etats_connus"  : len(self.Q),
        }

    # -----------------------------------------------------------------------
    # Sauvegarde / chargement
    # -----------------------------------------------------------------------
    def sauvegarder(self):
        if not self.chemin_save:
            return
        data = {
            "Q"          : self.Q,
            "epsilon"    : self.epsilon,
            "nb_parties" : self.nb_parties,
            "victoires"  : self.victoires[-500:],
            "scores"     : self.scores[-500:],
        }
        with open(self.chemin_save, "w") as f:
            json.dump(data, f)

    def _charger(self):
        try:
            with open(self.chemin_save) as f:
                d = json.load(f)
            self.Q          = d.get("Q", {})
            self.epsilon    = d.get("epsilon", EPS_INIT)
            self.nb_parties = d.get("nb_parties", 0)
            self.victoires  = d.get("victoires", [])
            self.scores     = d.get("scores", [])
        except Exception as e:
            print(f"[IA] Impossible de charger la sauvegarde : {e}")
