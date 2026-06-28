from flask_wtf import FlaskForm
from wtforms import SelectField, FloatField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Length


class SalesOrderForm(FlaskForm):
    customer_id = SelectField("Customer", coerce=int, validators=[DataRequired()])
    tax_percent = FloatField("Tax (%)", validators=[Optional(), NumberRange(min=0, max=100)])
    discount_amount = FloatField("Discount (Rs.)", validators=[Optional(), NumberRange(min=0)])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Create Invoice")


class PaymentForm(FlaskForm):
    amount = FloatField("Payment Amount", validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField("Record Payment")
