from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange


class WarehouseForm(FlaskForm):
    name = StringField("Warehouse Name", validators=[DataRequired(), Length(max=120)])
    location = StringField("Location", validators=[Optional(), Length(max=255)])
    capacity_meters = FloatField("Capacity (meters)", validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField("Save Warehouse")
