from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from Babylon.models import User, Plant, House
from flask_login import current_user


# validation functions below return validation errors in the form if the submitted name or email are already in use
class RegistrationForm(FlaskForm):
    name = StringField('Name',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first()
        if email:
            raise ValidationError('This email is taken, please choose another one')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class PlantForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    image = FileField('Picture (optional)', validators=[FileAllowed(['jpg', 'png'])])
    watering_frequency = IntegerField('Watering Frequency (days)', validators=[DataRequired()])

    submit = SubmitField('Add')


class HouseForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    address_first_line = StringField('Address')
    address_second_line = StringField('Address 2')
    postcode = StringField('Postcode')
    town = StringField('Town')

    submit = SubmitField('Add')


class DateWateredForm(FlaskForm):
    date_watered = DateField('Last Watered?', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Add')


class UpdateAccountForm(FlaskForm):
    name = StringField('Name',
                       validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_email(self, email):
        if email.data != current_user.email:
            email = User.query.filter_by(email=email.data).first()
            if email:
                raise ValidationError('This email is taken, please choose another one')

