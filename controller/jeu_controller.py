"""
CONTROLLER : jeu_controller.py
===============================
Orchestrateur MVC.
  - Reçoit les événements de la VUE (clics, boutons)
  - Interroge / modifie le MODÈLE (Plateau)
  - Met à jour la VUE via l'interface publique de celle-ci
  - Pilote les agents IA

La VUE ne connaît PAS le Modèle.
Le Modèle ne connaît PAS le Contrôleur ni la Vue.
"""

from __future__ import annotations
import threading
from model.plateau import Plateau, BLANC, NOIR
from ia.agent_ql  import AgentQL
from ia.entraineur import Entraineur

DELAI_IA_MS = 400   # délai entre les coups IA en mode visible


class JeuController:

    def __init__(self, vue):
        self.vue = vue

        # ── IA ──────────────────────────────────────────────────────────────
        self.ia_blanc = AgentQL(BLANC, "save_blanc.json")
        self.ia_noir  = AgentQL(NOIR,  "save_noir.json")

        # ── État courant ─────────────────────────────────────────────────────
        self.plateau          : Plateau | None = None
        self.mode             : str = "humain_vs_ia"  # ou "ia_vs_ia"
        self.joueur_courant   : int = BLANC
        self.partie_en_cours  : bool = False
        self.attente_ia       : bool = False

        # Sélection joueur humain
        self.pion_sel         = None
        self.mouvements_sel   : list = []

    # ── Démarrer une partie ─────────────────────────────────────────────────
    def nouvelle_partie(self, mode: str = "humain_vs_ia"):
        self.mode            = mode
        self.plateau         = Plateau()
        self.joueur_courant  = BLANC
        self.partie_en_cours = True
        self.attente_ia      = False
        self.pion_sel        = None
        self.mouvements_sel  = []

        self.vue.rafraichir_plateau(self.plateau, sel=None, destinations=[])
        self.vue.maj_scores(self.plateau.score(BLANC), self.plateau.score(NOIR))
        self.vue.set_message("Nouvelle partie ! " +
                              ("Votre tour (Blancs)" if mode == "humain_vs_ia"
                               else "IA vs IA — regardez les dames apprendre !"))
        self.vue.set_tour(self.joueur_courant)

        if mode == "ia_vs_ia":
            self.vue.apres(DELAI_IA_MS, self._coup_ia_visible)

    # ── Clic plateau (joueur humain) ────────────────────────────────────────
    def clic_case(self, ligne: int, col: int):
        if not self.partie_en_cours or self.mode != "humain_vs_ia":
            return
        if self.joueur_courant != BLANC or self.attente_ia:
            return

        cible = self.plateau.pion_en(ligne, col)

        # Sélectionner un pion du joueur
        if cible and cible.couleur == BLANC:
            tous = self.plateau.mouvements_legaux(BLANC)
            mvs_pion = [(p, ch) for p, ch in tous if p is cible]
            if not mvs_pion:
                self.vue.set_message("Ce pion n'a aucun mouvement disponible.")
                return
            self.pion_sel      = cible
            self.mouvements_sel = tous
            dests = [ch[-1] for _, ch in mvs_pion]
            self.vue.rafraichir_plateau(self.plateau,
                                         sel=(ligne, col), destinations=dests)
            return

        # Jouer sur une destination
        if self.pion_sel:
            for pion, chemin in self.mouvements_sel:
                if pion is self.pion_sel and chemin[-1] == (ligne, col):
                    self._jouer_coup_humain(pion, chemin)
                    return

        # Désélection
        self.pion_sel = None
        self.mouvements_sel = []
        self.vue.rafraichir_plateau(self.plateau, sel=None, destinations=[])

    def _jouer_coup_humain(self, pion, chemin):
        captures = self.plateau.appliquer(pion, chemin)
        self.pion_sel = None
        self.mouvements_sel = []
        self.vue.rafraichir_plateau(self.plateau, sel=None, destinations=[])
        self.vue.maj_scores(self.plateau.score(BLANC), self.plateau.score(NOIR))

        if captures:
            pts = sum(c.valeur for c in captures)
            self.vue.set_message(
                f"Vous capturez {len(captures)} pion(s) — +{pts} pt(s) !")
        else:
            self.vue.set_message("Coup joué.")

        if self._verifier_fin():
            return
        self.joueur_courant = NOIR
        self.vue.set_tour(NOIR)
        self.attente_ia = True
        self.vue.set_message("L'IA réfléchit…")
        self.vue.apres(DELAI_IA_MS, self._coup_ia_visible)

    # ── Coup IA (mode visible) ──────────────────────────────────────────────
    def _coup_ia_visible(self):
        if not self.partie_en_cours:
            return
        agent = self.ia_blanc if self.joueur_courant == BLANC else self.ia_noir
        choix = agent.choisir(self.plateau)
        if not choix:
            if self._verifier_fin():
                return
        else:
            pion, chemin = choix
            p_reel = self.plateau.pion_en(pion.ligne, pion.col)
            if p_reel:
                captures = self.plateau.appliquer(p_reel, chemin)
                agent.apprendre(self.plateau, captures, p_reel)
                self.vue.rafraichir_plateau(
                    self.plateau,
                    dernier_coup=chemin,
                    sel=None, destinations=[])
                self.vue.maj_scores(
                    self.plateau.score(BLANC), self.plateau.score(NOIR))
                if captures:
                    pts = sum(c.valeur for c in captures)
                    nom = "IA Blancs" if self.joueur_courant==BLANC else "IA Noirs"
                    self.vue.set_message(
                        f"{nom} capture {len(captures)} pion(s) — +{pts} pt(s) !")

        if self._verifier_fin():
            return

        self.joueur_courant = NOIR if self.joueur_courant == BLANC else BLANC
        self.vue.set_tour(self.joueur_courant)

        if self.mode == "ia_vs_ia":
            self.vue.apres(DELAI_IA_MS, self._coup_ia_visible)
        else:
            self.attente_ia = False
            self.vue.set_message("Votre tour !")

    # ── Vérification fin de partie ─────────────────────────────────────────
    def _verifier_fin(self) -> bool:
        g = self.plateau.gagnant()
        if g == 0:
            return False
        self.partie_en_cours = False
        sb = self.plateau.score(BLANC)
        sn = self.plateau.score(NOIR)
        self.ia_blanc.fin_partie(g)
        self.ia_noir.fin_partie(g)
        self.ia_blanc.sauvegarder()
        self.ia_noir.sauvegarder()
        self.vue.afficher_fin(g, sb, sn)
        return True

    # ── Entraînement rapide (thread) ────────────────────────────────────────
    def lancer_entrainement(self, n_parties: int):
        compteur = {"i": 0}

        def _cb(i, res):
            compteur["i"] = i
            if i % max(1, n_parties // 200) == 0:
                self.vue.root.after(0,
                    lambda i=i: self.vue.maj_progress_entrainement(
                        i, n_parties,
                        self.ia_blanc.stats(), self.ia_noir.stats()))

        def _run():
            e = Entraineur(self.ia_blanc, self.ia_noir, on_fin_partie=_cb)
            e.entrainer(n_parties)
            self.vue.root.after(0,
                lambda: self.vue.maj_progress_entrainement(
                    n_parties, n_parties,
                    self.ia_blanc.stats(), self.ia_noir.stats(),
                    termine=True))

        threading.Thread(target=_run, daemon=True).start()

    # ── Stats ───────────────────────────────────────────────────────────────
    def get_stats(self) -> dict:
        return {"blanc": self.ia_blanc.stats(), "noir": self.ia_noir.stats()}

    def reset_ia(self):
        import os
        self.ia_blanc = AgentQL(BLANC, "save_blanc.json")
        self.ia_noir  = AgentQL(NOIR,  "save_noir.json")
        for f in ("save_blanc.json", "save_noir.json"):
            if os.path.exists(f):
                os.remove(f)
