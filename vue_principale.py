"""
VIEW - vue_principale.py
Interface graphique du jeu de dames avec Tkinter.
Structure MVC : la vue ne contient aucune logique de jeu.
Elle reçoit des commandes du contrôleur et notifie les clics utilisateur.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from model.plateau import Plateau, BLANC, NOIR, DAME_BLANC, DAME_NOIR, TAILLE

# Palette de couleurs (thème bois élégant)
COULEUR_CASE_CLAIRE = "#F0D9B5"
COULEUR_CASE_FONCEE = "#B58863"
COULEUR_CASE_SELECTIONNEE = "#F6F669"
COULEUR_CASE_DESTINATION = "#CDD26A"
COULEUR_PION_BLANC = "#FAFAFA"
COULEUR_PION_BLANC_BORD = "#888888"
COULEUR_PION_NOIR = "#2C2C2C"
COULEUR_PION_NOIR_BORD = "#000000"
COULEUR_FOND = "#2B2B2B"
COULEUR_PANNEAU = "#1E1E1E"
COULEUR_TEXTE = "#E8E0D0"
COULEUR_ACCENT = "#D4A843"
COULEUR_TITRE = "#F0D9B5"

TAILLE_CASE = 72
TAILLE_PLATEAU = TAILLE * TAILLE_CASE
RAYON_PION = 28


class VuePrincipale:
    """Vue principale de l'application."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("♟ Jeu de Dames — IA Q-Learning")
        self.root.configure(bg=COULEUR_FOND)
        self.root.resizable(False, False)

        self.controller = None  # Sera injecté

        self._construire_interface()

    def set_controller(self, controller):
        """Injecte le contrôleur (injection de dépendance MVC)."""
        self.controller = controller

    # ─────────────────────────────────────────────
    #  Construction de l'interface
    # ─────────────────────────────────────────────

    def _construire_interface(self):
        """Construit toute l'interface graphique."""
        # Titre
        titre_frame = tk.Frame(self.root, bg=COULEUR_FOND)
        titre_frame.pack(pady=(16, 0))
        tk.Label(titre_frame, text="♟  JEU DE DAMES  ♟",
                 font=("Georgia", 22, "bold"), fg=COULEUR_TITRE,
                 bg=COULEUR_FOND).pack()
        tk.Label(titre_frame, text="Intelligence Artificielle par Q-Learning",
                 font=("Courier", 10), fg=COULEUR_ACCENT,
                 bg=COULEUR_FOND).pack()

        # Corps principal
        corps = tk.Frame(self.root, bg=COULEUR_FOND)
        corps.pack(padx=20, pady=12)

        # Panneau gauche : plateau
        self._construire_plateau(corps)

        # Panneau droit : contrôles et stats
        self._construire_panneau_droit(corps)

        # Barre de message
        self._construire_barre_message()

    def _construire_plateau(self, parent):
        """Construit le canvas du plateau de jeu."""
        plateau_frame = tk.Frame(parent, bg=COULEUR_FOND,
                                  bd=3, relief="ridge")
        plateau_frame.grid(row=0, column=0, padx=(0, 16))

        # Coordonnées horizontales
        coord_h_top = tk.Frame(plateau_frame, bg=COULEUR_FOND)
        coord_h_top.pack()
        tk.Label(coord_h_top, text="  ", bg=COULEUR_FOND).pack(side="left")
        for c in range(TAILLE):
            tk.Label(coord_h_top,
                     text=chr(ord('a') + c),
                     width=int(TAILLE_CASE / 8),
                     font=("Courier", 10),
                     fg=COULEUR_TEXTE, bg=COULEUR_FOND).pack(side="left")

        milieu = tk.Frame(plateau_frame, bg=COULEUR_FOND)
        milieu.pack()

        # Coordonnées verticales + canvas
        self.canvas = tk.Canvas(milieu,
                                 width=TAILLE_PLATEAU,
                                 height=TAILLE_PLATEAU,
                                 highlightthickness=0)
        self.canvas.pack(side="right")
        self.canvas.bind("<Button-1>", self._clic_canvas)

        # Labels de lignes
        coord_v = tk.Frame(milieu, bg=COULEUR_FOND)
        coord_v.pack(side="left")
        for i in range(TAILLE):
            tk.Label(coord_v,
                     text=str(TAILLE - i),
                     width=2,
                     font=("Courier", 10),
                     fg=COULEUR_TEXTE, bg=COULEUR_FOND).pack(
                expand=True, fill="y")

    def _construire_panneau_droit(self, parent):
        """Construit le panneau de droite (contrôles, scores, stats IA)."""
        self.panneau = tk.Frame(parent, bg=COULEUR_PANNEAU,
                                 width=280, bd=2, relief="groove")
        self.panneau.grid(row=0, column=1, sticky="nsew")
        self.panneau.pack_propagate(False)

        pad = {"padx": 14, "pady": 6}

        # ── Scores ──
        section_label(self.panneau, "SCORES").pack(**pad, anchor="w", pady=(14, 4))

        score_frame = tk.Frame(self.panneau, bg=COULEUR_PANNEAU)
        score_frame.pack(**pad)

        self.lbl_score_blanc = score_pion_label(score_frame, "Blancs", BLANC)
        self.lbl_score_blanc.grid(row=0, column=0, padx=8)
        self.lbl_score_noir = score_pion_label(score_frame, "Noirs", NOIR)
        self.lbl_score_noir.grid(row=0, column=1, padx=8)

        # ── Mode de jeu ──
        ttk.Separator(self.panneau, orient="horizontal").pack(
            fill="x", padx=10, pady=8)
        section_label(self.panneau, "MODE DE JEU").pack(**pad, anchor="w", pady=(0, 4))

        self.var_mode = tk.StringVar(value="joueur_vs_ia")
        modes = [("👤  Joueur vs IA", "joueur_vs_ia"),
                 ("🤖  IA vs IA (visible)", "ia_vs_ia")]
        for texte, val in modes:
            tk.Radiobutton(self.panneau, text=texte, variable=self.var_mode,
                           value=val, bg=COULEUR_PANNEAU, fg=COULEUR_TEXTE,
                           selectcolor=COULEUR_FOND,
                           activebackground=COULEUR_PANNEAU,
                           font=("Courier", 10)).pack(anchor="w", padx=14)

        btn_nouvelle = beau_bouton(self.panneau, "▶  Nouvelle partie",
                                    self._btn_nouvelle_partie)
        btn_nouvelle.pack(**pad, fill="x", pady=(8, 4))

        # ── Entraînement ──
        ttk.Separator(self.panneau, orient="horizontal").pack(
            fill="x", padx=10, pady=8)
        section_label(self.panneau, "ENTRAÎNEMENT IA").pack(
            **pad, anchor="w", pady=(0, 4))

        train_frame = tk.Frame(self.panneau, bg=COULEAU := COULEUR_PANNEAU)
        train_frame.pack(**pad, fill="x")
        tk.Label(train_frame, text="Parties :",
                 fg=COULEUR_TEXTE, bg=COULEUR_PANNEAU,
                 font=("Courier", 10)).grid(row=0, column=0, sticky="w")
        self.var_n_parties = tk.IntVar(value=100)
        spinbox = tk.Spinbox(train_frame, from_=10, to=5000, increment=50,
                              textvariable=self.var_n_parties, width=7,
                              bg="#333", fg=COULEUR_TEXTE, insertbackground="white",
                              font=("Courier", 10))
        spinbox.grid(row=0, column=1, padx=6)

        btn_train = beau_bouton(self.panneau, "⚡  Lancer entraînement",
                                 self._btn_entrainement, couleur="#8B6914")
        btn_train.pack(**pad, fill="x", pady=(4, 4))

        self.progress_train = ttk.Progressbar(self.panneau, mode="determinate",
                                               length=240)
        self.progress_train.pack(**pad, fill="x")

        # ── Stats IA ──
        ttk.Separator(self.panneau, orient="horizontal").pack(
            fill="x", padx=10, pady=8)
        section_label(self.panneau, "STATISTIQUES IA").pack(
            **pad, anchor="w", pady=(0, 4))

        self.texte_stats = tk.Text(self.panneau, height=10, width=30,
                                    bg="#111", fg="#AAD4A8",
                                    font=("Courier", 9), state="disabled",
                                    relief="flat", bd=0)
        self.texte_stats.pack(**pad)

        btn_stats = beau_bouton(self.panneau, "🔄  Actualiser stats",
                                 self._btn_actualiser_stats,
                                 couleur="#2A4A2A")
        btn_stats.pack(**pad, fill="x")

        # Reset
        ttk.Separator(self.panneau, orient="horizontal").pack(
            fill="x", padx=10, pady=8)
        btn_reset = beau_bouton(self.panneau, "🗑  Réinitialiser l'IA",
                                 self._btn_reset_ia, couleur="#5A1A1A")
        btn_reset.pack(**pad, fill="x", pady=(0, 14))

    def _construire_barre_message(self):
        """Barre de message en bas."""
        self.lbl_message = tk.Label(self.root,
                                     text="Bienvenue ! Choisissez un mode et lancez une partie.",
                                     font=("Georgia", 11, "italic"),
                                     fg=COULEUR_ACCENT, bg=COULEUR_FOND,
                                     wraplength=700, justify="center")
        self.lbl_message.pack(pady=(4, 14))

    # ─────────────────────────────────────────────
    #  Méthodes publiques appelées par le contrôleur
    # ─────────────────────────────────────────────

    def mettre_a_jour_plateau(self, plateau: Plateau,
                               pion_sel=None, destinations=None):
        """Redessine entièrement le plateau."""
        self.canvas.delete("all")
        dest_set = set(destinations) if destinations else set()

        for ligne in range(TAILLE):
            for col in range(TAILLE):
                x1 = col * TAILLE_CASE
                y1 = ligne * TAILLE_CASE
                x2 = x1 + TAILLE_CASE
                y2 = y1 + TAILLE_CASE

                # Couleur de la case
                if pion_sel and (ligne, col) == pion_sel:
                    couleur_case = COULEUR_CASE_SELECTIONNEE
                elif (ligne, col) in dest_set:
                    couleur_case = COULEUR_CASE_DESTINATION
                elif (ligne + col) % 2 == 0:
                    couleur_case = COULEUR_CASE_CLAIRE
                else:
                    couleur_case = COULEUR_CASE_FONCEE

                self.canvas.create_rectangle(x1, y1, x2, y2,
                                              fill=couleur_case, outline="")

                # Marquer les destinations possibles
                if (ligne, col) in dest_set:
                    cx, cy = x1 + TAILLE_CASE // 2, y1 + TAILLE_CASE // 2
                    self.canvas.create_oval(cx - 10, cy - 10,
                                             cx + 10, cy + 10,
                                             fill="#88AA22", outline="")

                # Dessiner le pion
                val = plateau.grille[ligne][col]
                if val != 0:
                    self._dessiner_pion(ligne, col, val)

    def _dessiner_pion(self, ligne: int, col: int, valeur: int):
        """Dessine un pion ou une dame sur la case."""
        cx = col * TAILLE_CASE + TAILLE_CASE // 2
        cy = ligne * TAILLE_CASE + TAILLE_CASE // 2
        r = RAYON_PION

        est_blanc = valeur in [BLANC, DAME_BLANC]
        est_dame = valeur in [DAME_BLANC, DAME_NOIR]

        fill = COULEUR_PION_BLANC if est_blanc else COULEUR_PION_NOIR
        outline = COULEUR_PION_BLANC_BORD if est_blanc else COULEUR_PION_NOIR_BORD
        accent = "#DDDDDD" if est_blanc else "#555555"

        # Ombre portée
        self.canvas.create_oval(cx - r + 3, cy - r + 3,
                                  cx + r + 3, cy + r + 3,
                                  fill="#00000055", outline="")
        # Corps
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                  fill=fill, outline=outline, width=2)
        # Reflet
        self.canvas.create_oval(cx - r + 6, cy - r + 6,
                                  cx - r + 16, cy - r + 16,
                                  fill=accent, outline="")

        # Couronne pour les dames
        if est_dame:
            couleur_couronne = COULEUR_ACCENT
            self.canvas.create_text(cx, cy, text="♛",
                                     font=("Arial", 18, "bold"),
                                     fill=couleur_couronne)

    def mettre_a_jour_scores(self, plateau: Plateau):
        """Met à jour les labels de score."""
        sb = plateau.score(BLANC)
        sn = plateau.score(NOIR)
        self.lbl_score_blanc.config(text=f"⬜ Blancs\n{sb} pts")
        self.lbl_score_noir.config(text=f"⬛ Noirs\n{sn} pts")

    def afficher_message(self, msg: str):
        """Affiche un message dans la barre du bas."""
        self.lbl_message.config(text=msg)

    def afficher_fin_partie(self, gagnant: int, score_blanc: int, score_noir: int):
        """Affiche une popup de fin de partie."""
        gagnant_txt = "Blancs ⬜" if gagnant == BLANC else "Noirs ⬛"
        messagebox.showinfo(
            "Fin de partie",
            f"Gagnant : {gagnant_txt}\n\n"
            f"Score Blancs : {score_blanc} points\n"
            f"Score Noirs : {score_noir} points\n\n"
            f"(1 pion = 1 point, 1 dame = 3 points)"
        )

    def afficher_stats(self, texte: str):
        """Affiche du texte dans le panneau de statistiques."""
        self.texte_stats.config(state="normal")
        self.texte_stats.delete("1.0", "end")
        self.texte_stats.insert("end", texte)
        self.texte_stats.config(state="disabled")

    def mettre_a_jour_progress(self, valeur: float):
        """Met à jour la barre de progression (0-100)."""
        self.progress_train["value"] = valeur

    def apres(self, delai_ms: int, callback):
        """Planifie un appel différé (pour l'IA)."""
        self.root.after(delai_ms, callback)

    # ─────────────────────────────────────────────
    #  Événements utilisateur
    # ─────────────────────────────────────────────

    def _clic_canvas(self, event):
        """Convertit un clic en coordonnées de case."""
        col = event.x // TAILLE_CASE
        ligne = event.y // TAILLE_CASE
        if self.controller:
            self.controller.clic_case(ligne, col)

    def _btn_nouvelle_partie(self):
        if self.controller:
            self.controller.nouvelle_partie(self.var_mode.get())

    def _btn_entrainement(self):
        if not self.controller:
            return
        n = self.var_n_parties.get()
        self.progress_train["value"] = 0
        self.progress_train["maximum"] = n
        compteur = [0]

        def callback_ui(n_partie, result, stats_blanc, stats_noir):
            compteur[0] = n_partie
            self.root.after(0, lambda: self._maj_progress_entrainement(
                n_partie, n, stats_blanc, stats_noir))

        self.afficher_message(f"Entraînement en cours ({n} parties)...")
        self.controller.lancer_entrainement(n, callback_ui)

    def _maj_progress_entrainement(self, i, total, sb, sn):
        self.progress_train["value"] = i
        if i == total:
            self.afficher_message(
                f"✅ Entraînement terminé ! "
                f"Blancs : {sb['taux_victoire']}% victoires | "
                f"Noirs : {sn['taux_victoire']}% victoires"
            )
            self._btn_actualiser_stats()

    def _btn_actualiser_stats(self):
        if not self.controller:
            return
        stats = self.controller.stats_ia()
        sb, sn = stats["blanc"], stats["noir"]
        texte = (
            f"─── IA Blanche ───\n"
            f"  Parties jouées : {sb['parties']}\n"
            f"  Victoires : {sb['victoires']}\n"
            f"  Taux victoire : {sb['taux_victoire']}%\n"
            f"  Score moy (50) : {sb['score_moyen']}\n"
            f"  Exploration ε : {sb['epsilon']}\n"
            f"  États connus : {sb['etats_connus']}\n\n"
            f"─── IA Noire ───\n"
            f"  Parties jouées : {sn['parties']}\n"
            f"  Victoires : {sn['victoires']}\n"
            f"  Taux victoire : {sn['taux_victoire']}%\n"
            f"  Score moy (50) : {sn['score_moyen']}\n"
            f"  Exploration ε : {sn['epsilon']}\n"
            f"  États connus : {sn['etats_connus']}\n"
        )
        self.afficher_stats(texte)

    def _btn_reset_ia(self):
        if messagebox.askyesno("Réinitialiser",
                                "Effacer tout l'apprentissage des IA ?"):
            if self.controller:
                from ia.agent_ql import AgentQL
                self.controller.ia_blanche = AgentQL(BLANC, fichier_q="save_blanc.json")
                self.controller.ia_noire = AgentQL(NOIR, fichier_q="save_noir.json")
                import os
                for f in ["save_blanc.json", "save_noir.json"]:
                    if os.path.exists(f):
                        os.remove(f)
                self.afficher_message("IA réinitialisée. Apprentissage repart de zéro.")
                self._btn_actualiser_stats()


# ─────────────────────────────────────────────
#  Widgets utilitaires
# ─────────────────────────────────────────────

def section_label(parent, texte: str) -> tk.Label:
    return tk.Label(parent, text=texte,
                    font=("Courier", 9, "bold"),
                    fg=COULEUR_ACCENT, bg=COULEUR_PANNEAU)


def beau_bouton(parent, texte: str, commande,
                couleur: str = "#4A3520") -> tk.Button:
    return tk.Button(parent, text=texte, command=commande,
                     bg=couleur, fg=COULEUR_TEXTE,
                     font=("Courier", 10, "bold"),
                     relief="flat", bd=0, pady=6,
                     cursor="hand2",
                     activebackground="#6A5540",
                     activeforeground="#FFFFFF")


def score_pion_label(parent, nom: str, couleur: int) -> tk.Label:
    bg = "#444" if couleur == BLANC else "#222"
    fg = COULEUR_TEXTE
    return tk.Label(parent, text=f"{'⬜' if couleur==BLANC else '⬛'} {nom}\n12 pts",
                    font=("Courier", 11, "bold"),
                    fg=fg, bg=bg, width=11,
                    relief="groove", bd=2, pady=6)
