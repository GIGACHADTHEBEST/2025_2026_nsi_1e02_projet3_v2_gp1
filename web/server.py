"""
Serveur Flask — interface web pour CheckersMind.
Lance avec : python web/server.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
from flask import Flask, jsonify, request, send_from_directory
from model.board import BoardState, CheckersNet
from model.rules import legal_moves, is_game_over, get_winner
from controller.self_play import NeuralAgent, MCTSAgent
from controller.trainer import load_model

app = Flask(__name__, static_folder='static')

# ─── Chargement du modèle ─────────────────────────────────────────────────
net = CheckersNet()
load_model(net)
ai_agent = MCTSAgent(net, num_simulations=150, temperature=0)

# ─── État de jeu partagé (une seule partie à la fois pour simplifier) ────
_game_state = None

def get_state():
    global _game_state
    if _game_state is None:
        _game_state = BoardState()
    return _game_state

def serialize_state(state):
    moves = legal_moves(state)
    return {
        'board': state.board,
        'current_player': state.current_player,
        'legal_moves': [[[r, c] for r, c in m] for m in moves],
        'game_over': is_game_over(state),
        'winner': get_winner(state) if is_game_over(state) else None,
        'whites': state.count_pieces()[0],
        'blacks': state.count_pieces()[1],
        'no_capture_count': state.no_capture_count,
    }

# ─── Routes ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/new_game', methods=['POST'])
def new_game():
    global _game_state
    _game_state = BoardState()
    return jsonify(serialize_state(_game_state))

@app.route('/api/state', methods=['GET'])
def get_game_state():
    return jsonify(serialize_state(get_state()))

@app.route('/api/move', methods=['POST'])
def make_move():
    """Le joueur humain envoie son coup."""
    state = get_state()
    data  = request.json
    # path : [[r0,c0],[r1,c1],...]
    path  = [tuple(sq) for sq in data['path']]

    moves = legal_moves(state)
    # Trouver le coup légal correspondant
    chosen = None
    for m in moves:
        if m[0] == path[0] and m[-1] == path[-1]:
            chosen = m
            break

    if chosen is None:
        return jsonify({'error': 'Coup illégal'}), 400

    state.apply_move(chosen)

    # Si c'est maintenant au tour de l'IA, on la fait jouer
    result = serialize_state(state)
    if not result['game_over'] and state.current_player == -1:
        ai_move = ai_agent.select_move(state)
        if ai_move:
            state.apply_move(ai_move)
            result = serialize_state(state)
            result['ai_move'] = [[r, c] for r, c in ai_move]

    return jsonify(result)

@app.route('/api/ai_move', methods=['POST'])
def ai_move():
    """Force l'IA à jouer (mode IA vs IA)."""
    state = get_state()
    if is_game_over(state):
        return jsonify(serialize_state(state))
    move = ai_agent.select_move(state)
    if move:
        state.apply_move(move)
    result = serialize_state(state)
    result['ai_move'] = [[r, c] for r, c in move] if move else None
    return jsonify(result)

@app.route('/api/reload_model', methods=['POST'])
def reload_model():
    """Recharge le modèle depuis le disque (après entraînement)."""
    global ai_agent
    load_model(net)
    ai_agent = MCTSAgent(net, num_simulations=150, temperature=0)
    return jsonify({'status': 'ok', 'message': 'Modèle rechargé'})

if __name__ == '__main__':
    print("\n  CheckersMind — Interface Web")
    print("  Ouvrez http://localhost:5000 dans votre navigateur\n")
    app.run(debug=False, port=5000)
