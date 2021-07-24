from flask import render_template
from owstats import app
from owstats.models import User

@app.route('/')
def index():
    return 'Index Page'

@app.route('/<username>')
def stats(username):
    # show the user profile for that user
    user = User.query.filter_by(username=username).first()
    if user:
        return render_template('user_stats.html', title=username, user=user)
    return 'User not found.'
