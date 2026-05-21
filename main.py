"""
main.py — Point d'entrée
========================
Assemble les trois couches MVC et démarre l'application.

     ┌──────────────┐       ┌──────────────────────┐
     │  VuePrincipale│◄─────│  JeuController        │
     │  (Tkinter)    │      │  (logique applicative)│
     └──────────────┘       └──────────┬───────────┘
                                        │ interroge/modifie
                                        ▼
                               ┌─────────────────┐
                               │  Plateau (Model)│
                               │  AgentQL  (IA)  │
                               └─────────────────┘
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from view.vue_principale   import VuePrincipale
from controller.jeu_controller import JeuController
from model.plateau         import Plateau


def main():
    root = tk.Tk()

    # 1. Créer la vue
    vue = VuePrincipale(root)

    # 2. Créer le contrôleur (injecte la vue)
    ctrl = JeuController(vue)

    # 3. Injecter le contrôleur dans la vue
    vue.set_controller(ctrl)

    # 4. Affichage initial
    p0 = Plateau()
    vue.rafraichir_plateau(p0, sel=None, destinations=[])
    vue.maj_scores(p0.score(1), p0.score(2))
    vue._on_stats()

    # 5. Centrer la fenêtre
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w,  h  = root.winfo_width(),       root.winfo_height()
    root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    root.mainloop()


if __name__ == "__main__":
    main()
