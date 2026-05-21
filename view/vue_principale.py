"""
VIEW : vue_principale.py
========================
Interface graphique Tkinter du jeu de dames.
Règles MVC strictes :
  - La vue NE connaît PAS le modèle Plateau directement
    (elle reçoit des données formatées par le contrôleur).
  - Elle expose une interface publique appelée par le contrôleur.
  - Elle délègue tous les événements au contrôleur.

Esthétique : bois sombre et or — élégant, intemporel.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from model.plateau import Plateau, BLANC, NOIR, DAME_B, DAME_N, N

# ── Palette ──────────────────────────────────────────────────────────────────
C = {
    "bg"           : "#1A1714",
    "panel"        : "#211E1B",
    "case_claire"  : "#E8C98A",
    "case_foncee"  : "#8B5E3C",
    "sel"          : "#F5E642",
    "dest"         : "#9DC13B",
    "dernierCoup"  : "#4DA6D8",
    "pion_b_fill"  : "#F2EDE4",
    "pion_b_bord"  : "#9A9080",
    "pion_n_fill"  : "#1C1C1C",
    "pion_n_bord"  : "#000000",
    "or"           : "#C9993A",
    "or_clair"     : "#E8C065",
    "texte"        : "#E8E0D0",
    "texte_dim"    : "#7A7060",
    "vert"         : "#5A9A4A",
    "rouge"        : "#9A3A3A",
    "sep"          : "#3A3530",
}

SZ  = 70   # taille d'une case en pixels
PAD = SZ * N

class VuePrincipale:
    """Vue principale — interface publique pour le contrôleur."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Jeu de Dames · IA Q-Learning")
        self.root.configure(bg=C["bg"])
        self.root.resizable(False, False)
        self.controller = None
        self._build()

    def set_controller(self, ctrl):
        self.controller = ctrl

    # ════════════════════════════════════════════════════════════════════════
    #  Construction de l'interface
    # ════════════════════════════════════════════════════════════════════════
    def _build(self):
        self._build_header()
        main = tk.Frame(self.root, bg=C["bg"])
        main.pack(padx=18, pady=0, fill="both")
        self._build_board(main)
        self._build_sidebar(main)
        self._build_footer()

    def _build_header(self):
        f = tk.Frame(self.root, bg=C["bg"])
        f.pack(pady=(14, 4))
        tk.Label(f, text="JEUX DE DAMES",
                 font=("Palatino Linotype", 24, "bold"),
                 fg=C["or_clair"], bg=C["bg"]).pack()
        tk.Label(f, text="Intelligence Artificielle  ·  Q-Learning",
                 font=("Courier New", 10), fg=C["texte_dim"], bg=C["bg"]).pack()

    def _build_board(self, parent):
        wrap = tk.Frame(parent, bg=C["bg"])
        wrap.grid(row=0, column=0, padx=(0, 16), pady=8)

        # Repères colonnes (a-h)
        top_coords = tk.Frame(wrap, bg=C["bg"])
        top_coords.pack()
        tk.Label(top_coords, text="  ", bg=C["bg"]).pack(side="left")
        for c in range(N):
            tk.Label(top_coords, text=chr(ord('a')+c), width=int(SZ/9)+1,
                     font=("Courier New", 10), fg=C["texte_dim"],
                     bg=C["bg"]).pack(side="left")

        row_wrap = tk.Frame(wrap, bg=C["bg"])
        row_wrap.pack()

        # Repères lignes (8-1)
        self._row_labels = tk.Frame(row_wrap, bg=C["bg"])
        self._row_labels.pack(side="left")
        for i in range(N):
            tk.Label(self._row_labels, text=str(N-i), width=2,
                     font=("Courier New", 10), fg=C["texte_dim"],
                     bg=C["bg"]).pack(expand=True, fill="y")

        # Canvas principal
        self.canvas = tk.Canvas(row_wrap, width=PAD, height=PAD,
                                 highlightthickness=2,
                                 highlightbackground=C["or"])
        self.canvas.pack(side="left")
        self.canvas.bind("<Button-1>", self._on_clic)

    def _build_sidebar(self, parent):
        self.sidebar = tk.Frame(parent, bg=C["panel"], width=270,
                                 bd=0, relief="flat")
        self.sidebar.grid(row=0, column=1, sticky="ns", pady=8)
        self.sidebar.pack_propagate(False)

        sp = {"padx": 16, "pady": 5}

        # ── Scores ──────────────────────────────────────────────
        self._section("SCORES", self.sidebar)
        sf = tk.Frame(self.sidebar, bg=C["panel"])
        sf.pack(**sp)
        self.lbl_sc_b = self._score_badge(sf, "⬜ Blancs", "12")
        self.lbl_sc_b.grid(row=0, column=0, padx=6)
        self.lbl_sc_n = self._score_badge(sf, "⬛ Noirs", "12")
        self.lbl_sc_n.grid(row=0, column=1, padx=6)

        # Tour actuel
        self.lbl_tour = tk.Label(self.sidebar, text="Tour : —",
                                  font=("Courier New", 10, "bold"),
                                  fg=C["or"], bg=C["panel"])
        self.lbl_tour.pack(**sp)

        self._sep(self.sidebar)

        # ── Mode ────────────────────────────────────────────────
        self._section("MODE DE JEU", self.sidebar)
        self.var_mode = tk.StringVar(value="humain_vs_ia")
        for txt, val in [("👤  Joueur (Blancs) vs IA", "humain_vs_ia"),
                          ("🤖  IA vs IA  (visible)", "ia_vs_ia")]:
            tk.Radiobutton(self.sidebar, text=txt, variable=self.var_mode,
                           value=val, bg=C["panel"], fg=C["texte"],
                           selectcolor=C["bg"], activebackground=C["panel"],
                           font=("Courier New", 10)).pack(anchor="w", padx=16)
        self._bouton("▶  Nouvelle partie", self._on_nouvelle_partie,
                     self.sidebar, C["or"]).pack(**sp, fill="x", pady=(8,4))

        self._sep(self.sidebar)

        # ── Entraînement ─────────────────────────────────────────
        self._section("ENTRAÎNEMENT RAPIDE", self.sidebar)
        ef = tk.Frame(self.sidebar, bg=C["panel"])
        ef.pack(**sp, fill="x")
        tk.Label(ef, text="Parties :", fg=C["texte"], bg=C["panel"],
                 font=("Courier New", 10)).pack(side="left")
        self.var_n = tk.IntVar(value=500)
        tk.Spinbox(ef, from_=50, to=10000, increment=50,
                   textvariable=self.var_n, width=7,
                   bg="#2E2A26", fg=C["texte"],
                   insertbackground="white",
                   font=("Courier New", 10)).pack(side="left", padx=8)

        self._bouton("⚡  Lancer entraînement", self._on_entrainement,
                     self.sidebar, "#5A3E10").pack(**sp, fill="x")
        self.pb = ttk.Progressbar(self.sidebar, mode="determinate", length=230)
        self.pb.pack(**sp, fill="x")

        self._sep(self.sidebar)

        # ── Stats ────────────────────────────────────────────────
        self._section("STATISTIQUES IA", self.sidebar)
        self.txt_stats = tk.Text(self.sidebar, height=11, width=28,
                                  bg="#111", fg="#8DC88A",
                                  font=("Courier New", 9),
                                  state="disabled", relief="flat", bd=0,
                                  insertbackground="white")
        self.txt_stats.pack(**sp)
        self._bouton("↺  Actualiser stats", self._on_stats,
                     self.sidebar, "#1E3A1E").pack(**sp, fill="x")

        self._sep(self.sidebar)
        self._bouton("🗑  Réinitialiser l'IA", self._on_reset,
                     self.sidebar, "#3A1010").pack(**sp, fill="x", pady=(0,14))

    def _build_footer(self):
        self.lbl_msg = tk.Label(
            self.root,
            text="Bienvenue ! Choisissez un mode puis lancez une partie.",
            font=("Palatino Linotype", 11, "italic"),
            fg=C["or_clair"], bg=C["bg"], wraplength=740)
        self.lbl_msg.pack(pady=(2, 14))

    # ════════════════════════════════════════════════════════════════════════
    #  Interface publique (appelée par le contrôleur)
    # ════════════════════════════════════════════════════════════════════════

    def rafraichir_plateau(self, plateau: Plateau,
                            sel=None, destinations=None,
                            dernier_coup=None):
        """Redessine entièrement le plateau."""
        self.canvas.delete("all")
        dests = set(destinations or [])
        dernier = set(dernier_coup or [])

        for l in range(N):
            for c in range(N):
                x1, y1 = c*SZ, l*SZ
                x2, y2 = x1+SZ, y1+SZ
                pos = (l, c)

                if sel and pos == sel:
                    bg = C["sel"]
                elif pos in dests:
                    bg = C["dest"]
                elif pos in dernier:
                    bg = C["dernierCoup"]
                elif (l+c) % 2 == 0:
                    bg = C["case_claire"]
                else:
                    bg = C["case_foncee"]

                self.canvas.create_rectangle(x1, y1, x2, y2,
                                              fill=bg, outline="")

                # Point de destination
                if pos in dests:
                    cx, cy = x1+SZ//2, y1+SZ//2
                    self.canvas.create_oval(cx-9, cy-9, cx+9, cy+9,
                                             fill="#6A9A20", outline="")

                # Pion
                v = plateau.grille[l][c]
                if v:
                    self._draw_piece(l, c, v)

    def _draw_piece(self, l: int, c: int, v: int):
        cx = c*SZ + SZ//2
        cy = l*SZ + SZ//2
        r  = SZ//2 - 7
        blanc = v in (BLANC, DAME_B)
        fill  = C["pion_b_fill"] if blanc else C["pion_n_fill"]
        bord  = C["pion_b_bord"] if blanc else C["pion_n_bord"]
        hl    = "#EEEEEE"        if blanc else "#3A3A3A"

        # Ombre
        self.canvas.create_oval(cx-r+3, cy-r+3, cx+r+3, cy+r+3,
                                  fill="#00000066", outline="")
        # Corps
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                                  fill=fill, outline=bord, width=2)
        # Reflet
        self.canvas.create_oval(cx-r+5, cy-r+5, cx-r+14, cy-r+14,
                                  fill=hl, outline="")
        # Couronne dame
        if v in (DAME_B, DAME_N):
            self.canvas.create_text(cx, cy, text="♛",
                                     font=("Arial", int(SZ*0.32), "bold"),
                                     fill=C["or"])

    def maj_scores(self, score_blanc: int, score_noir: int):
        self.lbl_sc_b.config(text=f"⬜ Blancs\n{score_blanc} pts")
        self.lbl_sc_n.config(text=f"⬛ Noirs\n{score_noir} pts")

    def set_message(self, msg: str):
        self.lbl_msg.config(text=msg)

    def set_tour(self, couleur: int):
        nom = "Blancs ⬜" if couleur == BLANC else "Noirs ⬛"
        self.lbl_tour.config(text=f"Tour : {nom}")

    def afficher_fin(self, gagnant: int, score_blanc: int, score_noir: int):
        nom = "Blancs ⬜" if gagnant == BLANC else "Noirs ⬛"
        self.set_message(f"Partie terminée — Gagnant : {nom} !")
        messagebox.showinfo("Fin de partie",
            f"Gagnant : {nom}\n\n"
            f"Score Blancs : {score_blanc} pt(s)\n"
            f"Score Noirs  : {score_noir} pt(s)\n\n"
            f"Rappel : 1 pion = 1 pt, 1 dame = 3 pts")

    def maj_progress_entrainement(self, i: int, total: int,
                                   stats_b: dict, stats_n: dict,
                                   termine: bool = False):
        self.pb["maximum"] = total
        self.pb["value"]   = i
        if termine:
            self.set_message(
                f"✅ Entraînement terminé ({total} parties) — "
                f"Blancs {stats_b['taux_victoire']}% / "
                f"Noirs {stats_n['taux_victoire']}% victoires")
            self._afficher_stats(stats_b, stats_n)
        else:
            self.set_message(
                f"Entraînement : {i}/{total} parties… "
                f"ε={stats_b['epsilon']:.3f}")

    def _afficher_stats(self, sb: dict, sn: dict):
        txt = (
            f"── IA Blanche ──────────\n"
            f"  Parties    : {sb['parties']}\n"
            f"  Victoires  : {sb['taux_victoire']}%\n"
            f"  Score moy  : {sb['score_moyen']}\n"
            f"  Epsilon ε  : {sb['epsilon']}\n"
            f"  États Q    : {sb['etats_connus']}\n\n"
            f"── IA Noire ────────────\n"
            f"  Parties    : {sn['parties']}\n"
            f"  Victoires  : {sn['taux_victoire']}%\n"
            f"  Score moy  : {sn['score_moyen']}\n"
            f"  Epsilon ε  : {sn['epsilon']}\n"
            f"  États Q    : {sn['etats_connus']}\n"
        )
        self.txt_stats.config(state="normal")
        self.txt_stats.delete("1.0", "end")
        self.txt_stats.insert("end", txt)
        self.txt_stats.config(state="disabled")

    # ════════════════════════════════════════════════════════════════════════
    #  Événements → délégués au contrôleur
    # ════════════════════════════════════════════════════════════════════════
    def _on_clic(self, evt):
        if self.controller:
            self.controller.clic_case(evt.y // SZ, evt.x // SZ)

    def _on_nouvelle_partie(self):
        if self.controller:
            self.controller.nouvelle_partie(self.var_mode.get())

    def _on_entrainement(self):
        if self.controller:
            self.pb["value"] = 0
            self.set_message("Entraînement lancé…")
            self.controller.lancer_entrainement(self.var_n.get())

    def _on_stats(self):
        if self.controller:
            s = self.controller.get_stats()
            self._afficher_stats(s["blanc"], s["noir"])

    def _on_reset(self):
        if messagebox.askyesno("Réinitialiser",
                                "Effacer tout l'apprentissage des IA ?"):
            if self.controller:
                self.controller.reset_ia()
                self.set_message("IA remise à zéro.")

    def apres(self, ms: int, fn):
        self.root.after(ms, fn)

    # ════════════════════════════════════════════════════════════════════════
    #  Widgets utilitaires (privés)
    # ════════════════════════════════════════════════════════════════════════
    def _section(self, titre: str, parent):
        tk.Label(parent, text=titre,
                 font=("Courier New", 8, "bold"),
                 fg=C["or"], bg=C["panel"]).pack(
            padx=16, pady=(10, 2), anchor="w")

    def _sep(self, parent):
        tk.Frame(parent, bg=C["sep"], height=1).pack(
            fill="x", padx=10, pady=6)

    def _bouton(self, texte: str, cmd, parent, couleur: str) -> tk.Button:
        return tk.Button(parent, text=texte, command=cmd,
                         bg=couleur, fg=C["texte"],
                         font=("Courier New", 10, "bold"),
                         relief="flat", bd=0, pady=7, cursor="hand2",
                         activebackground="#8A6A30",
                         activeforeground="#FFFFFF")

    def _score_badge(self, parent, label: str, val: str) -> tk.Label:
        return tk.Label(parent,
                        text=f"{label}\n{val} pts",
                        font=("Courier New", 11, "bold"),
                        fg=C["texte"], bg="#2E2A26",
                        width=12, relief="groove", bd=2, pady=6)
