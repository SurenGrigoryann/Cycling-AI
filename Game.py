from flask import Blueprint, render_template, jsonify, send_from_directory, current_app
import os

game_bp = Blueprint('game', __name__)


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


@game_bp.route('/game/asset/<filename>')
def serve_game_asset(filename):
    allowed = {'organictrash.png', 'papertrash.png', 'wastetrash.png', 'backgroundfinal.jpg', 'correctsound.mp3', 'wrongsound.mp3'}
    if filename not in allowed:
        return 'Not found', 404
    return send_from_directory(os.path.join(current_app.root_path, 'asset'), filename)
