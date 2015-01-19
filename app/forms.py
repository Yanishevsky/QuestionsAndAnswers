from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, TextAreaField
from wtforms.validators import Required


class LoginForm(Form):
    openid = TextField('openid', validators = [Required()])
    remember_me = BooleanField('remember_me', default = False)


class QuestionForm(Form):
    question = TextField('question', validators = [Required()])


class AnswerForm(Form):
    answer = TextAreaField('answer', validators = [Required()])

