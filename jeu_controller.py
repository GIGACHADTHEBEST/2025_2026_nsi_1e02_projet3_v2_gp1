"""
CONTROLLER - jeu_controller.py
Fait le lien entre le Modèle (plateau, IA) et la Vue (interface graphique).
Gère le déroulement d'une partie, les modes de jeu, les tours.
"""

from model.plateau import Plateau, BLANC, NOIR
from ia.agent_ql import AgentQL
from ia.entraineur import Entraineur
import threading


class JeuController:
    """
    Contrôleur principal du jeu de dames.
    
    Modes disponibles :
    - "joueur_vs_ia" : le joueur humain joue contre l'IA
    - "ia_vs_ia" : deux IA jouent l'une contre l'autre (entraînement visible)
    - "entrainement" : entraînement rapide en arrière-plan
    """

    DELAI_IA = 600  # ms entre chaque coup de l'IA (mode visible)

    def __init__(self, vue):
        """
        vue : instance de la vue principale (VuePrincipale)
        """
        self.vue = vue
        self.plateau = Plateau()
        self.mode = "joueur_vs_ia"

        # Agents IA
        self.ia_blanche = AgentQL(BLANC, fichier_q="save_blanc.json")
        self.ia_noire = AgentQL(NOIR, fichier_q="save_noir.json")

        self.joueur_couleur = BLANC    # Le joueur humain joue les blancs
        self.joueur_courant = BLANC    # Qui doit jouer maintenant
        self.partie_active = False
        self.en_attente_ia = False

        # Sélection en cours (pour le joueur humain)
        self.pion_selectionne = None
        self.mouvements_disponibles = []  # [(pion, chemin), ...]

        # Stats globales
        self.nb_parties = 0
        self.victoires_joueur = 0
        self.victoires_ia = 0

    def nouvelle_partie(self, mode: str = None):
        """Démarre une nouvelle partie."""
        if mode:
            self.mode = mode

        self.plateau = Plateau()
        self.joueur_courant = BLANC
        self.partie_active = True
        self.pion_selectionne = None
        self.mouvements_disponibles = []
        self.en_attente_ia = False

        self.vue.mettre_a_jour_plateau(self.plateau)
        self.vue.afficher_message(
            f"Nouvelle partie ! "
            f"{'Votre tour (Blancs)' if self.mode == 'joueur_vs_ia' else 'IA vs IA'}"
        )
        self.vue.mettre_a_jour_scores(self.plateau)

        # Si l'IA commence
        if self.mode == "ia_vs_ia":
            self.vue.apres(self.DELAI_IA, self._coup_ia)
        elif self.mode == "joueur_vs_ia" and self.joueur_couleur != BLANC:
            self.vue.apres(self.DELAI_IA, self._coup_ia)

    def clic_case(self, ligne: int, col: int):
        """
        Appelé quand le joueur clique sur une case.
        Gère la sélection d'un pion et l'exécution d'un mouvement.
        """
        if not self.partie_active or self.mode != "joueur_vs_ia":
            return
        if self.joueur_courant != self.joueur_couleur:
            return
        if self.en_attente_ia:
            return

        pion_clique = self.plateau.get_pion(ligne, col)

        # Cas 1 : Le joueur clique sur un de ses pions → sélection
        if pion_clique and pion_clique.couleur == self.joueur_couleur:
            self._selectionner_pion(pion_clique)
            return

        # Cas 2 : Le joueur clique sur une destination valide → jouer
        if self.pion_selectionne:
            for pion, chemin in self.mouvements_disponibles:
                if pion == self.pion_selectionne and chemin[-1] == (ligne, col):
                    self._jouer_mouvement(pion, chemin)
                    return

        # Cas 3 : Clic invalide → désélectionner
        self.pion_selectionne = None
        self.mouvements_disponibles = []
        self.vue.mettre_a_jour_plateau(self.plateau)

    def _selectionner_pion(self, pion):
        """Sélectionne un pion et affiche ses mouvements possibles."""
        tous_mouvements = self.plateau.mouvements_possibles(self.joueur_couleur)

        # Filtrer les mouvements de ce pion
        mouvements_pion = [(p, ch) for p, ch in tous_mouvements if p == pion]

        if not mouvements_pion:
            self.vue.afficher_message("Ce pion ne peut pas bouger !")
            return

        self.pion_selectionne = pion
        self.mouvements_disponibles = tous_mouvements  # Garder tous pour validation
        destinations = [ch[-1] for _, ch in mouvements_pion]

        self.vue.mettre_a_jour_plateau(self.plateau,
                                        pion_sel=(pion.ligne, pion.col),
                                        destinations=destinations)

    def _jouer_mouvement(self, pion, chemin: list):
        """Exécute un mouvement du joueur humain."""
        captures = self.plateau.appliquer_mouvement(pion, chemin)
        self.pion_selectionne = None
        self.mouvements_disponibles = []

        self.vue.mettre_a_jour_plateau(self.plateau)
        self.vue.mettre_a_jour_scores(self.plateau)

        if captures:
            self.vue.afficher_message(
                f"Vous avez capturé {len(captures)} pion(s) ! "
                f"+{sum(c.valeur() for c in captures)} points"
            )

        self._verifier_fin()
        if self.partie_active:
            self.joueur_courant = self.ia_noire.couleur
            self.vue.afficher_message("Tour de l'IA...")
            self.en_attente_ia = True
            self.vue.apres(self.DELAI_IA, self._coup_ia)

    def _coup_ia(self):
        """Exécute un coup de l'IA."""
        if not self.partie_active:
            return

        # Choisir quel agent joue
        if self.joueur_courant == BLANC:
            agent = self.ia_blanche
        else:
            agent = self.ia_noire

        choix = agent.choisir_action(self.plateau)
        if choix is None:
            self._verifier_fin()
            return

        pion, chemin = choix
        score_avant = self.plateau.score(self.joueur_courant)

        captures = self.plateau.appliquer_mouvement(pion, chemin)

        # Calculer récompense
        recompense = sum(c.valeur() for c in captures)
        if pion.est_dame:
            recompense += AgentQL.RECOMPENSE_PROMOTION if len(chemin) <= 2 else 0
        agent.apprendre(self.plateau, recompense)

        self.vue.mettre_a_jour_plateau(self.plateau)
        self.vue.mettre_a_jour_scores(self.plateau)

        if self.mode == "ia_vs_ia" and captures:
            couleur_nom = "Blancs" if self.joueur_courant == BLANC else "Noirs"
            self.vue.afficher_message(
                f"IA {couleur_nom} capture {len(captures)} pion(s) !"
            )

        self._verifier_fin()
        if not self.partie_active:
            return

        # Passer au joueur suivant
        self.joueur_courant = NOIR if self.joueur_courant == BLANC else BLANC

        if self.mode == "ia_vs_ia":
            self.vue.apres(self.DELAI_IA, self._coup_ia)
        elif self.mode == "joueur_vs_ia":
            if self.joueur_courant != self.joueur_couleur:
                self.vue.apres(self.DELAI_IA, self._coup_ia)
            else:
                self.en_attente_ia = False
                self.vue.afficher_message("Votre tour !")

    def _verifier_fin(self):
        """Vérifie si la partie est terminée et agit en conséquence."""
        gagnant = self.plateau.partie_terminee()
        if gagnant == 0:
            return

        self.partie_active = False
        self.nb_parties += 1

        score_blanc = self.plateau.score(BLANC)
        score_noir = self.plateau.score(NOIR)

        # Notifier les agents
        self.ia_blanche.fin_de_partie(gagnant, score_blanc)
        self.ia_noire.fin_de_partie(gagnant, score_noir)

        # Sauvegarder automatiquement
        self.ia_blanche.sauvegarder("save_blanc.json")
        self.ia_noire.sauvegarder("save_noir.json")

        # Message de fin
        if self.mode == "joueur_vs_ia":
            if gagnant == self.joueur_couleur:
                self.victoires_joueur += 1
                msg = f"🎉 Vous avez GAGNÉ ! Score : Vous {score_blanc} - IA {score_noir}"
            else:
                self.victoires_ia += 1
                msg = f"😔 L'IA a gagné. Score : Vous {score_blanc} - IA {score_noir}"
        else:
            gagnant_nom = "Blancs" if gagnant == BLANC else "Noirs"
            msg = f"Partie terminée ! Gagnant : {gagnant_nom} | Blancs : {score_blanc} pts | Noirs : {score_noir} pts"

        self.vue.afficher_message(msg)
        self.vue.afficher_fin_partie(gagnant, score_blanc, score_noir)

    def lancer_entrainement(self, n_parties: int, callback_ui):
        """Lance l'entraînement en arrière-plan (thread séparé)."""
        def _run():
            entraineur = Entraineur(
                self.ia_blanche, self.ia_noire,
                callback_progression=callback_ui
            )
            entraineur.entrainer(n_parties, sauvegarder_tous=50)
            self.ia_blanche.sauvegarder("save_blanc.json")
            self.ia_noire.sauvegarder("save_noir.json")

        t = threading.Thread(target=_run, daemon=True)
        t.start()

    def stats_ia(self) -> dict:
        """Retourne les statistiques des deux IA."""
        return {
            "blanc": self.ia_blanche.stats(),
            "noir": self.ia_noire.stats()
        }
