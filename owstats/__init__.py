import os

from flask import Flask, flash, redirect, render_template, url_for, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from owstats.forms import AddUserForm


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('OWSTATS_DB')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


from owstats.models import CompStats, Player, Season
from owstats.utils import get_api_response, make_plot, get_player_seasons


@app.route('/')
def index():
    users = Player.query.filter_by(active=1).order_by(Player.etime.desc()).all()
    users = users + Player.query.filter_by(active=2).all()    # inactive
    users = users + Player.query.filter_by(active=3).all()    # private

    return render_template('select_user.html', title='Select user', legend='Select user', users=users)


@app.route('/add', methods=['GET', 'POST'])
def add_user():
    form = AddUserForm()
    if form.validate_on_submit():
        # Do we have this user already?
        user = Player.query.filter_by(username=form.username.data).first()
        if user:
            flash(
                f'User {user.username} already exists. Here are their collected.', 'success')
            return redirect(url_for('stats', username=user.username))

        # User not in DB yet, let's check if they exist in OW
        try:
            response = get_api_response(
                form.platform.data, form.region.data, form.username.data)
        except:
            flash(f'Problems encountered when adding the user. Make sure the user exists on that platform/region.', 'warning')
            return redirect(url_for('index'))

        if response:
            r_json = response.json()

            if 'error' in r_json:
                flash(f"Error returned from API: {r_json['error']}", 'warning')
                return redirect(url_for('index'))

            if not r_json['private']:
                user = Player()
                user.username = form.username.data
                user.region = form.region.data
                user.platform = form.platform.data
                user.games_played = r_json['competitiveStats']['games']['played']
                user.endorsement = r_json['endorsement']
                user.icon = r_json['icon']
                db.session.add(user)
                db.session.commit()

                current_season = Season.query.order_by(Season.etime.desc()).first()

                cs = CompStats()
                cs.season = current_season.season
                cs.games_played = user.games_played
                cs.games_won = r_json['competitiveStats']['games']['won']
                cs.rating_avg = r_json['rating']
                if 'ratings' in r_json and r_json['ratings'] is not None:
                    for rating in r_json['ratings']:
                        if rating['role'] == 'tank':
                            cs.rating_tank = rating['level'] or None
                        if rating['role'] == 'damage':
                            cs.rating_damage = rating['level'] or None
                        if rating['role'] == 'support':
                            cs.rating_support = rating['level'] or None
                else: 
                    cs.rating_tank = None
                    cs.rating_damage = None
                    cs.rating_support = None

                cs.player = user

                db.session.add(cs)
                db.session.commit()
                make_plot(user)

                flash(
                    f'User {user.username} has been added to the database.', 'success')
                return redirect(url_for('stats', username=user.username))
        flash(f"No response from API received. Check connection or something? User not added.", 'warning')
        return redirect(url_for('index'))
    form.username.data = request.args.get('username')
    return render_template('add_user.html', title='Add user', legend='Add user', form=form)


@app.route('/<username>')
@app.route('/<username>/<int:season>')
def stats(username, season=0):
    # show the user profile for that user
    user = Player.query.filter_by(username=username).first()
    if season == 0:
        season = Season.query.order_by(Season.etime.desc()).first().season
    seasons = get_player_seasons(username)
    if user:
        return render_template('user_stats.html', title=username, user=user, season=season, seasons=seasons)

    form = AddUserForm()
    form.username.data = username
    flash(
        f"Player {username} doesn't exist in the database. Check spelling or add them.", 'warning')
    return redirect(url_for('add_user', username=username))


@app.route('/chart/<username>')
@app.route('/chart/<username>/<int:season>')
def chart(username, season=0):
    # show the user profile for that user
    user = Player.query.filter_by(username=username).first()
    if season == 0:
        season = Season.query.order_by(Season.etime.desc()).first().season
    seasons = get_player_seasons(username)
    if user:
        plot_fn = f"{user.username}_{user.platform}_{user.region}_{season}.png"
        return render_template('user_plots.html', title=username, user=user, plot_fn=plot_fn, season=season, seasons=seasons)
