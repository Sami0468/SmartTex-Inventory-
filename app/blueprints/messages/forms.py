from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length


class MessageForm(FlaskForm):
    body = TextAreaField("Message", validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField("Send")
