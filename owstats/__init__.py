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
        player = Player.query.filter_by(username=form.username.data).first()
        if player:
            flash(
                f'Player {player.username} already exists. Here are their collected.', 'success')
            return redirect(url_for('stats', username=player.username))

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
                player = Player()
                player.username = form.username.data
                player.region = form.region.data
                player.platform = form.platform.data
                player.games_played = r_json['competitiveStats']['games']['played']
                player.endorsement = r_json['endorsement']
                player.icon = r_json['icon']
                db.session.add(player)
                db.session.commit()

                current_season = Season.query.order_by(Season.etime.desc()).first()

                cs = CompStats()
                cs.season = current_season.season
                cs.games_played = player.games_played
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

                cs.player = player

                db.session.add(cs)
                db.session.commit()
                make_plot(player)

                flash(
                    f'Player {player.username} has been added to the database.', 'success')
                return redirect(url_for('stats', username=player.username))
        flash(f"No response from API received. Check connection or something? Player not added.", 'warning')
        return redirect(url_for('index'))
    form.username.data = request.args.get('username')
    return render_template('add_user.html', title='Add player', legend='Add player', form=form)


@app.route('/<username>')
@app.route('/<username>/<int:season>')
def stats(username, season=0):
    # show the player profile for that player
    player = Player.query.filter_by(username=username).first()
    if season == 0:
        season = Season.query.order_by(Season.etime.desc()).first().season
    seasons = get_player_seasons(username)
    if player:
        return render_template('user_stats.html', title=username, user=player, season=season, seasons=seasons)

    form = AddUserForm()
    form.username.data = username
    flash(
        f"Player {username} doesn't exist in the database. Check spelling or add them.", 'warning')
    return redirect(url_for('add_user', username=username))


@app.route('/chart/<username>')
@app.route('/chart/<username>/<int:season>')
def chart(username, season=0):
    # show the player profile for that player
    player = Player.query.filter_by(username=username).first()
    if season == 0:
        season = Season.query.order_by(Season.etime.desc()).first().season
    seasons = get_player_seasons(username)
    if player:
        plot_fn = f"{player.username}_{player.platform}_{player.region}_{season}.png"
        return render_template('user_plots.html', title=username, user=player, plot_fn=plot_fn, season=season, seasons=seasons)
