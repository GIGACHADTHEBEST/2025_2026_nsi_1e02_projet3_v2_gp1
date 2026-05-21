"""
main.py — Point d'entrée du jeu de dames
Instancie les composants MVC et démarre l'application.

Architecture MVC :
  Model      → model/plateau.py     (état du jeu, règles)
  View       → view/vue_principale.py (interface Tkinter)
  Controller → controller/jeu_controller.py (logique applicative)
  IA         → ia/agent_ql.py        (Q-Learning)
               ia/entraineur.py      (auto-entraînement)
"""

import tkinter as tk
import sys
import os

# Ajouter le répertoire courant au chemin Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from view.vue_principale import VuePrincipale
from controller.jeu_controller import JeuController


def main():
    """Lance l'application."""
    # Créer la fenêtre Tkinter
    root = tk.Tk()

    # Créer la vue
    vue = VuePrincipale(root)

    # Créer le contrôleur et l'injecter dans la vue
    controller = JeuController(vue)
    vue.set_controller(controller)

    # Afficher les stats initiales
    vue._btn_actualiser_stats()

    # Dessiner le plateau vide initial
    from model.plateau import Plateau
    vue.mettre_a_jour_plateau(Plateau())

    # Centrer la fenêtre
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    root.mainloop()


if __name__ == "__main__":
    main()
