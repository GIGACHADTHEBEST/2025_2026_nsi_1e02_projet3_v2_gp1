"""
IA : agent_ql.py
================
Agent Q-Learning optimisé pour une progression RAPIDE.

Techniques pour accélérer l'apprentissage :
  1. Alpha élevé (0.3) → apprend vite des nouvelles expériences
  2. Epsilon decay rapide (0.98/partie) → exploite tôt ce qu'il sait
  3. Récompenses denses : chaque capture, chaque promotion récompensée
  4. Reward shaping : bonus de position (avancer = +0.05, dame = +0.3)
  5. Expérience replay léger (mémorise les N dernières transitions)
  6. Heuristique initiale : valeur Q = heuristique(état) si état inconnu

Objectif : 1 pion = 1 point, maximiser les points capturés.
"""

from __future__ import annotations
import random
import json
import os
from collections import deque
from model.plateau import Plateau, BLANC, NOIR, VALEUR_PION, VALEUR_DAME, N

# ── Hyperparamètres ──────────────────────────────────────────────────────────
ALPHA        = 0.30    # taux d'apprentissage (élevé = progression rapide)
GAMMA        = 0.92    # discount futur
EPS_INIT     = 0.90    # exploration initiale
EPS_MIN      = 0.05    # exploration minimale
EPS_DECAY    = 0.980   # décroissance rapide → exploite vite
REPLAY_SIZE  = 2000    # taille du buffer d'expérience
REPLAY_BATCH = 32      # taille du mini-batch de replay

# ── Récompenses ──────────────────────────────────────────────────────────────
R_PION      = 1.0    # capturer un pion adverse
R_DAME      = 3.0    # capturer une dame adverse
R_PROMO     = 2.5    # devenir dame
R_WIN       = 10.0   # gagner la partie
R_LOSE      = -10.0  # perdre
R_AVANCE    = 0.05   # avancer d'une rangée (reward shaping)


class AgentQL:
    """
    Agent Q-Learning avec reward shaping et experience replay léger.
    Converge significativement en ~200-500 parties.
    """

    def __init__(self, couleur: int, chemin_save: str | None = None):
        self.couleur      = couleur
        self.adverse      = NOIR if couleur == BLANC else BLANC
        self.chemin_save  = chemin_save

        # Table Q  {cle_etat: {cle_action: float}}
        self.Q: dict[str, dict[str, float]] = {}

        self.epsilon       = EPS_INIT
        self.nb_parties    = 0
        self.scores        : list[float] = []   # pts capturés par partie
        self.victoires     : list[int]   = []   # 1/0 par partie
        self.pts_cette_partie = 0.0

        # Buffer de replay (s, a, r, s', done)
        self._replay: deque = deque(maxlen=REPLAY_SIZE)

        # Mémo du dernier pas
        self._s  : str | None = None
        self._a  : str | None = None
        self._l_avant: int = 0   # ligne avant le coup (reward shaping)

        if chemin_save and os.path.exists(chemin_save):
            self._charger()

    # ── Table Q ─────────────────────────────────────────────────────────────
    def _q(self, s: str, a: str) -> float:
        return self.Q.get(s, {}).get(a, 0.0)

    def _set_q(self, s: str, a: str, v: float):
        if s not in self.Q:
            self.Q[s] = {}
        self.Q[s][a] = v

    # ── Encodage action ─────────────────────────────────────────────────────
    @staticmethod
    def _cle_action(chemin: list) -> str:
        return "_".join(f"{l}{c}" for l, c in chemin)

    # ── Heuristique initiale ─────────────────────────────────────────────────
    def _heuristique(self, plateau: Plateau) -> float:
        """
        Estimation rapide de la qualité d'une position.
        Utilisé pour initialiser Q si l'état est inconnu.
        """
        sc = plateau.score(self.couleur) - plateau.score(self.adverse)
        # Bonus de position : pions plus avancés vers la promotion
        bonus = 0.0
        for p in plateau.pions[self.couleur]:
            rang = (N - 1 - p.ligne) if self.couleur == BLANC else p.ligne
            bonus += rang * 0.02
        return sc + bonus

    # ── Choisir une action ──────────────────────────────────────────────────
    def choisir(self, plateau: Plateau):
        """
        Stratégie epsilon-greedy.
        Retourne (pion, chemin) ou None.
        """
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
                # Si état inconnu, utiliser heuristique simulée
                if v == 0.0 and s not in self.Q:
                    sim = plateau.copie()
                    sim.appliquer(sim.pion_en(pion.ligne, pion.col) or pion,
                                  chemin)
                    v = self._heuristique(sim) * 0.1
                if v > best_v:
                    best_v = v
                    best   = (pion, chemin)
            choix = best

        self._s = s
        self._a = self._cle_action(choix[1])
        self._l_avant = choix[0].ligne
        return choix

    # ── Apprendre après un coup ─────────────────────────────────────────────
    def apprendre(self, plateau_apres: Plateau, captures, pion_joue):
        """Mise à jour Q après un coup. Appelé par le contrôleur."""
        if self._s is None:
            return

        # ── Récompense immédiate ──
        r = 0.0
        for cap in captures:
            r += R_DAME if cap.est_dame else R_PION
        if pion_joue.est_dame and not any(
                True for _ in captures):  # vient juste d'être promu
            # on détecte la promotion via la ligne d'arrivée
            pass
        if pion_joue.est_dame:
            l_promo = 0 if self.couleur == BLANC else N-1
            if pion_joue.ligne == l_promo:
                r += R_PROMO

        # Reward shaping : avancer
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

        # Stocker dans le replay buffer
        self._replay.append((self._s, self._a, r, s2,
                              [self._cle_action(ch) for _, ch in mvs2], done))

        # Mise à jour directe (TD)
        self._td_update(self._s, self._a, r, s2,
                        [self._cle_action(ch) for _, ch in mvs2])

        # Experience replay
        if len(self._replay) >= REPLAY_BATCH:
            self._experience_replay()

        self._s = None
        self._a = None

    def _td_update(self, s, a, r, s2, actions2):
        q_now = self._q(s, a)
        q_max = max((self._q(s2, a2) for a2 in actions2), default=0.0)
        new_q = q_now + ALPHA * (r + GAMMA * q_max - q_now)
        self._set_q(s, a, new_q)

    def _experience_replay(self):
        batch = random.sample(self._replay, REPLAY_BATCH)
        for s, a, r, s2, actions2, done in batch:
            q_max = 0.0 if done else max(
                (self._q(s2, a2) for a2 in actions2), default=0.0)
            q_now = self._q(s, a)
            self._set_q(s, a, q_now + ALPHA * (r + GAMMA * q_max - q_now))

    # ── Fin de partie ───────────────────────────────────────────────────────
    def fin_partie(self, gagnant: int):
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

    # ── Statistiques ───────────────────────────────────────────────────────
    def stats(self) -> dict:
        n = self.nb_parties
        v50 = self.victoires[-50:]
        s50 = self.scores[-50:]
        return {
            "parties"       : n,
            "taux_victoire" : round(sum(v50)/max(1,len(v50))*100, 1),
            "score_moyen"   : round(sum(s50)/max(1,len(s50)), 2),
            "epsilon"       : round(self.epsilon, 3),
            "etats_connus"  : len(self.Q),
        }

    # ── Sauvegarde / chargement ─────────────────────────────────────────────
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
            print(f"[IA] Chargement échoué : {e}")
