from flask import Blueprint, render_template

practice_bp = Blueprint('practice', __name__)

@practice_bp.route('/practice')
def practice():
    return render_template('practice.html')
