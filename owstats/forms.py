from flask_wtf import FlaskForm
from wtforms import RadioField, StringField, SubmitField
from wtforms.validators import InputRequired

class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    region = RadioField('Region', choices=[('us', 'US'), ('eu', 'EU'), ('asia', 'Asia')], validators=[InputRequired()])
    platform = RadioField('Platform', choices=[('psn', 'Playstation'), ('xbl', 'XBox'), ('pc', 'PC'), ('nintendo-switch','Nintendo Switch')], validators=[InputRequired()])
    submit = SubmitField('Add user')