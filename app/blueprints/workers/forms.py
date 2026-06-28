from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

DEPARTMENTS = ["Cutting", "Stitching", "Dyeing", "Finishing", "Packing", "Quality Assurance",
               "Warehouse", "Maintenance", "Administration"]


class WorkerForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    cnic = StringField("CNIC / National ID", validators=[Optional(), Length(max=20)])
    phone = StringField("Phone Number", validators=[Optional(), Length(max=30)])
    department = SelectField("Department", choices=[(d, d) for d in DEPARTMENTS], validators=[DataRequired()])
    designation = StringField("Designation", validators=[Optional(), Length(max=80)])
    base_salary = FloatField("Base Salary (monthly, Rs.)", validators=[DataRequired(), NumberRange(min=0)])
    date_joined = DateField("Date Joined", validators=[Optional()])
    submit = SubmitField("Save Worker")


class AttendanceForm(FlaskForm):
    date = DateField("Date", validators=[DataRequired()])
    status = SelectField("Status", choices=[(s, s) for s in
        ("Present", "Absent", "Half-Day", "Leave")], validators=[DataRequired()])
    hours_worked = FloatField("Hours Worked", validators=[Optional(), NumberRange(min=0, max=24)])
    overtime_hours = FloatField("Overtime Hours", validators=[Optional(), NumberRange(min=0, max=24)])
    submit = SubmitField("Mark Attendance")


class PayrollForm(FlaskForm):
    month = StringField("Month (YYYY-MM)", validators=[DataRequired(), Length(max=7)])
    overtime_pay = FloatField("Overtime Pay", validators=[Optional(), NumberRange(min=0)])
    deductions = FloatField("Deductions", validators=[Optional(), NumberRange(min=0)])
    bonus = FloatField("Bonus", validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField("Generate Payroll")
