from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, SelectField, HiddenField, FloatField, FormField, FieldList
from wtforms.validators import DataRequired, InputRequired, NumberRange, ValidationError
from .models import currencies, currency_choices_form

def validate_currency(form, field):
    if field.data == "":
        raise ValidationError("Sorry, you haven't chosen a currency!")

def validate_stock_option(form, field):
    if(field.data != 0 and field.data != 1):
        raise ValidationError("Sorry, you haven't chosen an option!")

class LoginForm(FlaskForm):
   team_name = StringField("Team Name", validators=[DataRequired()] )
   password = PasswordField("Password", validators=[DataRequired()])

class AdminLoginForm(FlaskForm):
    user = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])

class ForexForm(FlaskForm):
    from_currency = SelectField('From', coerce=int, choices=currency_choices_form, validators=[validate_currency])

    to_currency = SelectField('To', coerce=int, choices=currency_choices_form, validators=[validate_currency])

    amount = FloatField("Amount", validators=[InputRequired(), NumberRange(min=0)])

    round = HiddenField()
    started_at = HiddenField()


stonk_options=[ (0, "Buy"), (1, "Sell")]
class StockForm(FlaskForm):
    option = SelectField("Option", coerce=int, choices=stonk_options, validators=[validate_stock_option])
    qty = IntegerField("Amount", validators=[InputRequired(), NumberRange(min=0)])


class StockForm_Full(FlaskForm):
    stox = FieldList(FormField(StockForm), min_entries=2, max_entries=2)

    round = HiddenField()
    started_at = HiddenField()
