# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired

class TestForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    subject = SelectField('Предмет', choices=[
        ('math', 'Математика'),
        ('russian', 'Русский язык'),
    ], validators=[DataRequired()])
    submit = SubmitField('Добавить тест')