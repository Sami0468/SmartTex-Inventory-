from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Length


class ProductionOrderForm(FlaskForm):
    product_name = StringField("Product Name", validators=[DataRequired(), Length(max=150)])
    fabric_id = SelectField("Fabric to Use", coerce=int, validators=[DataRequired()])
    quantity_required_meters = FloatField("Quantity Required (meters)", validators=[DataRequired(), NumberRange(min=0.01)])
    assigned_team = StringField("Assigned Team", validators=[Optional(), Length(max=120)])
    start_date = DateField("Start Date", validators=[Optional()])
    deadline = DateField("Deadline", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Create Production Order")


class ProductionUpdateForm(FlaskForm):
    status = SelectField("Status", choices=[(s, s) for s in
        ("Pending", "Approved", "In Progress", "Completed", "Delayed")], validators=[DataRequired()])
    quantity_used_meters = FloatField("Fabric Used So Far (meters)", validators=[Optional(), NumberRange(min=0)])
    waste_meters = FloatField("Waste (meters)", validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField("Update Production")
