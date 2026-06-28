from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, SubmitField, DateField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length, Email, NumberRange


class SupplierForm(FlaskForm):
    company_name = StringField("Company Name", validators=[DataRequired(), Length(max=150)])
    contact_person = StringField("Contact Person", validators=[Optional(), Length(max=100)])
    phone = StringField("Phone Number", validators=[Optional(), Length(max=30)])
    email = StringField("Email Address", validators=[Optional(), Email(), Length(max=120)])
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    country = StringField("Country", validators=[Optional(), Length(max=80)])
    rating = FloatField("Rating (0–5)", validators=[Optional(), NumberRange(min=0, max=5)])
    submit = SubmitField("Save Supplier")


class PurchaseOrderForm(FlaskForm):
    supplier_id = SelectField("Supplier", coerce=int, validators=[DataRequired()])
    expected_date = DateField("Expected Delivery Date", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Create Purchase Order")


class POItemForm(FlaskForm):
    fabric_id = SelectField("Fabric", coerce=int, validators=[Optional()])
    description = StringField("Description", validators=[Optional(), Length(max=150)])
    quantity_meters = FloatField("Quantity (meters)", validators=[DataRequired(), NumberRange(min=0.01)])
    unit_cost = FloatField("Unit Cost", validators=[DataRequired(), NumberRange(min=0)])


class PaymentForm(FlaskForm):
    amount = FloatField("Payment Amount", validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField("Record Payment")
