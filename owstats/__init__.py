import os

from flask import Flask, flash, redirect, render_template, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from owstats.forms import AddUserForm
from owstats.utils import get_api_response, make_plot

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('OWSTATS_DB')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


from owstats.models import CompStats, User, Season

@app.route('/')
def index():
    users = User.query.order_by(User.etime.desc()).all()
    return render_template('select_user.html', title='Select user', legend='Select user', users=users)


@app.route('/add', methods=['GET', 'POST'])
def add_user():
    form = AddUserForm()
    if form.validate_on_submit():
        # Do we have this user already?
        user = User.query.filter_by(username=form.username.data).first()
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
                user = User()
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
                            cs.rating_tank = rating['level']
                        if rating['role'] == 'damage':
                            cs.rating_damage = rating['level']
                        if rating['role'] == 'support':
                            cs.rating_support = rating['level']
                else:
                    cs.rating_tank = 0
                    cs.rating_damage = 0
                    cs.rating_support = 0

                cs.player = user

                db.session.add(cs)
                db.session.commit()
                make_plot(user)

                flash(
                    f'User {user.username} has been added to the database.', 'success')
                return redirect(url_for('stats', username=user.username))
        flash(f"No response from API received. Check connection or something? User not added.", 'warning')
        return redirect(url_for('index'))
    return render_template('add_user.html', title='Add user', legend='Add user', form=form)


@app.route('/<username>')
def stats(username):
    # show the user profile for that user
    user = User.query.filter_by(username=username).first()
    if user:
        return render_template('user_stats.html', title=username, user=user)

    form = AddUserForm()
    form.username.data = username
    flash(
        f"Player {username} doesn't exist in the database. Check spelling or add them.", 'warning')
    return render_template('add_user.html', title='Add user', legend='Add user', form=form)


@app.route('/<username>/chart')
def chart(username):
    # show the user profile for that user
    user = User.query.filter_by(username=username).first()
    if user:
        plot_fn = f"{user.username}_{user.platform}_{user.region}_{user.comp_stats[0].season}.png"
        return render_template('user_plots.html', title=username, user=user, plot_fn=plot_fn)
