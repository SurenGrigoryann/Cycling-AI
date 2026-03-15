from flask import Blueprint, render_template, jsonify, send_from_directory, current_app, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from auth import get_db
import os

game_bp = Blueprint('game', __name__)

def init_scores_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS game_scores (
            username TEXT PRIMARY KEY,
            best_score INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_scores_table()


@game_bp.route('/game')
def game():
    return render_template('game.html')


@game_bp.route('/game/api/items')
def game_items():
    base = os.path.join(current_app.root_path, 'asset', 'emoji_only_organics_paper_waste_200_png')
    items = []
    for category in ('organics', 'paper', 'waste'):
        folder = os.path.join(base, category)
        if not os.path.isdir(folder):
            continue
        for fname in sorted(os.listdir(folder)):
            if fname.lower().endswith('.png'):
                items.append({
                    'file': fname,
                    'category': category,
                    'url': f'/game/emoji/{category}/{fname}'
                })
    return jsonify({'items': items})


@game_bp.route('/game/emoji/<category>/<filename>')
def serve_emoji(category, filename):
    if category not in ('organics', 'paper', 'waste'):
        return 'Not found', 404
    directory = os.path.join(current_app.root_path, 'asset', 'emoji_only_organics_paper_waste_200_png', category)
    return send_from_directory(directory, filename)


@game_bp.route('/game/score', methods=['GET'])
@jwt_required()
def get_score():
    username = get_jwt_identity()
    conn = get_db()
    row = conn.execute('SELECT best_score FROM game_scores WHERE username = ?', (username,)).fetchone()
    conn.close()
    return jsonify({'best_score': row['best_score'] if row else 0})

@game_bp.route('/game/score', methods=['POST'])
@jwt_required()
def save_score():
    username = get_jwt_identity()
    data = request.get_json()
    new_score = int(data.get('score', 0))
    conn = get_db()
    row = conn.execute('SELECT best_score FROM game_scores WHERE username = ?', (username,)).fetchone()
    is_new_record = False
    if row is None:
        conn.execute('INSERT INTO game_scores (username, best_score) VALUES (?, ?)', (username, new_score))
        is_new_record = new_score > 0
    elif new_score > row['best_score']:
        conn.execute('UPDATE game_scores SET best_score = ? WHERE username = ?', (new_score, username))
        is_new_record = True
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'is_new_record': is_new_record})

@game_bp.route('/game/leaderboard')
def leaderboard():
    conn = get_db()
    rows = conn.execute(
        'SELECT username, best_score FROM game_scores ORDER BY best_score DESC LIMIT 10'
    ).fetchall()
    conn.close()
    return jsonify({'leaderboard': [{'username': r['username'], 'score': r['best_score']} for r in rows]})

@game_bp.route('/game/asset/<filename>')
def serve_game_asset(filename):
    allowed = {'organictrash.png', 'papertrash.png', 'wastetrash.png', 'backgroundfinal.jpg', 'correctsound.mp3', 'wrongsound.mp3'}
    if filename not in allowed:
        return 'Not found', 404
    return send_from_directory(os.path.join(current_app.root_path, 'asset'), filename)
