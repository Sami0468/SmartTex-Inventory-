from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Length

FABRIC_TYPES = ["Cotton", "Polyester", "Silk", "Denim", "Linen", "Wool", "Rayon",
                "Viscose", "Chiffon", "Velvet", "Jersey", "Fleece", "Lawn", "Blended"]


class FabricForm(FlaskForm):
    name = StringField("Fabric Name", validators=[DataRequired(), Length(max=120)])
    fabric_type = SelectField("Fabric Type", choices=[(t, t) for t in FABRIC_TYPES],
                               validators=[DataRequired()])
    gsm = IntegerField("GSM (g/m²)", validators=[Optional(), NumberRange(min=0)])
    width_inches = FloatField("Width (inches)", validators=[Optional(), NumberRange(min=0)])
    color = StringField("Color", validators=[Optional(), Length(max=40)])
    pattern = StringField("Pattern", validators=[Optional(), Length(max=60)])
    roll_number = StringField("Roll Number", validators=[Optional(), Length(max=40)])

    quantity_meters = FloatField("Quantity (meters)", validators=[DataRequired(), NumberRange(min=0)])
    unit_cost = FloatField("Unit Cost (per meter)", validators=[DataRequired(), NumberRange(min=0)])
    selling_price = FloatField("Selling Price (per meter)", validators=[DataRequired(), NumberRange(min=0)])
    low_stock_threshold = FloatField("Low Stock Threshold (meters)", validators=[Optional(), NumberRange(min=0)])

    warehouse_id = SelectField("Warehouse", coerce=int, validators=[DataRequired()])
    supplier_id = SelectField("Supplier", coerce=int, validators=[Optional()])

    submit = SubmitField("Save Fabric")


class StockAdjustmentForm(FlaskForm):
    movement_type = SelectField("Movement Type", choices=[
        ("IN", "Stock In (received)"),
        ("OUT", "Stock Out (manual deduction)"),
        ("ADJUSTMENT", "Adjustment (correction)"),
        ("DAMAGE", "Mark as Damaged"),
    ], validators=[DataRequired()])
    quantity_meters = FloatField("Quantity (meters)", validators=[DataRequired(), NumberRange(min=0.01)])
    note = StringField("Note / Reason", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Apply Movement")


class TransferForm(FlaskForm):
    to_warehouse_id = SelectField("Transfer To Warehouse", coerce=int, validators=[DataRequired()])
    quantity_meters = FloatField("Quantity (meters)", validators=[DataRequired(), NumberRange(min=0.01)])
    note = StringField("Note", validators=[Optional(), Length(max=255)])
    submit = SubmitField("Transfer Stock")
