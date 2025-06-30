from flask import render_template
from routefind import bp

@bp.route('/routefind')
def find_route():
    return render_template('routefind/index.html') 