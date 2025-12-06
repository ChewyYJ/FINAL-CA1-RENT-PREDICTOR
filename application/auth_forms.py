
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField

from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp
 
class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(), Length(min=3, max=64)
    ])

    email = StringField("Email", validators=[
        DataRequired(),
        Email(message="Please enter a valid email address."),
        Length(max=120),
        Regexp(r'.+@gmail\.com$', message="Email must end with @gmail.com.")
    ])

    password = PasswordField("Password", validators=[
        DataRequired(),
        Length(min=6, message="Password must be at least 6 characters.")
    ])

    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo('password', message="Passwords do not match.")
    ])

    submit = SubmitField("Create Account")



class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(message="Please enter a valid email address."),
            Regexp(r'.+@gmail\.com$', message="Email must end with @gmail.com.")
        ]
    )
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Log In")
