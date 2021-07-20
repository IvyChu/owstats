from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///OWstatsLite.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)

    # platform 	The game platform (pc, etc)
    # region 	The game region (us, eu, asia)
    # battletag 	Your battlenet tag, replacing the # with a -

    battletag = db.Column(db.String(20), unique=True, nullable=True)

    # battletag doesn't seem to work for psn at the moment
    username = db.Column(db.String(20), unique=True, nullable=False)
    region = db.Column(db.String(10), unique=False, nullable=False)
    platform = db.Column(db.String(10), unique=False, nullable=False)

    icon = db.Column(db.String(200), unique=True, nullable=True)

    endorsement = db.Column(db.Integer)

    games_played = db.Column(db.Integer, default=0)

    comp_stats = db.relationship('CompStats', backref='player', lazy=True)

    active = db.Column(db.Integer, default=1) # 0 if inactive, 1 if active

    ctime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return '<User %r>' % self.username


class CompStats(db.Model):
    __tablename__ = 'comp_stats'
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    games_played = db.Column(db.Integer)
    games_won = db.Column(db.Integer)

    rating_avg = db.Column(db.Integer)
    rating_tank = db.Column(db.Integer)
    rating_damage = db.Column(db.Integer)
    rating_support = db.Column(db.Integer)

    ctime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<CompStats games: {self.games_played}, open: {self.rating_avg}, tank: {self.rating_tank}, dps: {self.rating_damage}, support: {self.rating_support}>'


@app.route('/')
def index():
    return 'Index Page'

@app.route('/stats/<username>')
def stats(username):
    # show the user profile for that user
    return f'User {username}'