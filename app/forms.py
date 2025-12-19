from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError

from .models.user import User


class RegistrationForm(FlaskForm):
    name = StringField('ФИО', validators=[DataRequired(), Length(min=2, max=100)])
    login = StringField('Логин', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

    def validate_login(self, login):
        user = User.query.filter_by(login=login.data).first()
        if user:
            raise ValidationError('Логин занят')


class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class CityForm(FlaskForm):
    city = StringField('Город', validators=[DataRequired(), Length(min=2, max=100)])
    submit = SubmitField('Показать погоду')