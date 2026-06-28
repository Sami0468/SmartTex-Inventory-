from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, Email


class CustomerForm(FlaskForm):
    name = StringField("Customer Name", validators=[DataRequired(), Length(max=120)])
    company_name = StringField("Company Name", validators=[Optional(), Length(max=150)])
    phone = StringField("Phone Number", validators=[Optional(), Length(max=30)])
    email = StringField("Email Address", validators=[Optional(), Email(), Length(max=120)])
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Save Customer")
