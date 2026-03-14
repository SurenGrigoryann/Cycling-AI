from flask import Blueprint, render_template

learning_bp = Blueprint('learning', __name__)

@learning_bp.route('/learning')
def learning():
    return render_template('learning.html')

@learning_bp.route('/lesson/1')
def lesson1():
    return render_template('lesson1.html')

@learning_bp.route('/lesson/2')
def lesson2():
    return render_template('lesson2.html')

@learning_bp.route('/lesson/3')
def lesson3():
    return render_template('lesson3.html')