from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from forms import LoginForm, QuestionForm, AnswerForm
from models import User, ROLE_USER, ROLE_ADMIN, Question, Answer
from datetime import datetime
from config import POSTS_PER_PAGE

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated():
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()

@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/', methods = ['GET', 'POST'])
@app.route('/home', methods = ['GET', 'POST'])
@app.route('/home/<int:page>', methods = ['GET', 'POST'])
def home(page = 1):
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(body = form.question.data, timestamp = datetime.utcnow(), author = g.user)
        db.session.add(question)
        db.session.commit()
        flash('Your question is published!')
        return redirect(url_for('home'))
    questions = Question.query.order_by(Question.timestamp.desc()).paginate(page, POSTS_PER_PAGE, False)
    return render_template('home.html', title = 'Home', form = form, questions = questions)

@app.route('/login', methods = ['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for = ['nickname', 'email'])
    return render_template('login.html', title = 'Sign In', form = form, providers = app.config['OPENID_PROVIDERS'])

@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    user = User.query.filter_by(email = resp.email).first()

    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        nickname = User.make_unique_nickname(nickname)
        nickname = nickname.title()
        user = User(nickname = nickname, email = resp.email, role = ROLE_USER)
        db.session.add(user)
        db.session.commit()
    remember_me = False

    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    return redirect(request.args.get('next') or url_for('home'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/rating/<qid>/<aid>')
@app.route('/rating/<qid>/<page>/<aid>')
@login_required
def rating(qid, aid, page = 1):
    answer = Answer.query.filter_by(id=aid).first()

    if not answer.like():
        db.session.add(answer)
        db.session.commit()

    return redirect(url_for('question', qid=qid, page=page))

@app.route('/question/<qid>', methods = ['GET', 'POST'])
@app.route('/question/<qid>/<int:page>', methods = ['GET', 'POST'])
def question(qid, page = 1):
    form = AnswerForm()
    question = Question.query.filter_by(id=qid).first()

    if form.validate_on_submit():
        answer = Answer(body = form.answer.data, timestamp = datetime.utcnow(), author = g.user, question = question, rating=0)
        db.session.add(answer)
        db.session.commit()
        flash('Your answer is published!')
        return redirect(url_for('question', qid=qid))
    answers = Answer.query.filter_by(question_id=qid).order_by(Answer.timestamp.desc()).paginate(page, POSTS_PER_PAGE, False)
    return render_template('question.html', form = form, answers = answers, question = question)
