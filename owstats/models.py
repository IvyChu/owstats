from datetime import datetime

from owstats import db


class Season(db.Model):
    __tablename__ = 'seasons'
    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.Integer)
    next_switch_date = db.Column(db.DateTime, nullable=True)  # find out online
    ctime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    etime = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Season {self.season}, next_switch_date:{self.next_switch_date:%Y-%m-%d %H:%M}, etime:{self.etime:%Y-%m-%d %H:%M}>'


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

    icon = db.Column(db.String(200), unique=False, nullable=True)

    endorsement = db.Column(db.Integer)

    games_played = db.Column(db.Integer, default=0)

    comp_stats = db.relationship('CompStats', backref='player', lazy=True)

    active = db.Column(db.Integer, default=1) # 0 if inactive, 1 if active

    ctime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    etime = db.Column(db.DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<User %r>' % self.username

    def get_win_percentage(self):
        latest_stats = self.comp_stats[-1]
        games_played = latest_stats.games_played
        games_won = latest_stats.games_won
        return round((games_won/games_played)*100, 2)



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

    season = db.Column(db.Integer)

    def __repr__(self):
        return f'<CompStats games: {self.games_played}, open: {self.rating_avg}, tank: {self.rating_tank}, dps: {self.rating_damage}, support: {self.rating_support}>'
