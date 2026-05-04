# 2025_2026_nsi_1e02_projet3_v2_gp1
Jermolajs ADARCENKO
Raphaël BOTALLA-GAMBETTA
Gwenole BEILLEVAIRE 

ChessMind est un moteur d'échecs en Python capable d'apprendre à jouer par lui-même grâce au self-play et à l'apprentissage par renforcement. Inspiré du principe d'AlphaZero, le programme joue des milliers de parties contre lui-même, analyse ses erreurs, et améliore progressivement sa stratégie — sans jamais avoir été programmé avec des règles d'ouverture ou de tactique.
Moteur de règles complet (déplacements, roque, prise en passant, promotion, échec/mat/pat)
Réseau de neurones évaluant les positions (entrée : plateau encodé, sortie : score + probabilités de coups)
Boucle de self-play : l'IA joue contre elle-même et génère ses propres données d'entraînement
Entraînement itératif : plus elle joue, plus elle s'améliore
Interface en terminal (ou optionnellement graphique avec pygame)
Sauvegarde et chargement des modèles entraînés