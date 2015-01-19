from app import db

ROLE_USER = 0
ROLE_ADMIN = 1

voted_users = db.Table('voted_users',
                       db.Column('answer_id', db.Integer, db.ForeignKey('answer.id')),
                       db.Column('voted_id', db.Integer, db.ForeignKey('user.id'))
                       )

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(64), unique = True)
    email = db.Column(db.String(120), index = True, unique = True)
    role = db.Column(db.SmallInteger, default = ROLE_USER)
    questions = db.relationship('Question', backref = 'author', lazy = 'dynamic')
    answers = db.relationship('Answer', backref = 'author', lazy = 'dynamic')

    @staticmethod
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname = nickname).first() == None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname = new_nickname).first() == None:
                break
            version += 1
        return new_nickname
        
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.nickname)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.String(60))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    answers = db.relationship('Answer', backref = 'question', lazy = 'dynamic')

    def __repr__(self):
        return '<Post %r>' % (self.body)


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    body = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime)
    rating = db.Column(db.Integer)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    voted = db.relationship('Answer',
        secondary = voted_users,
        primaryjoin = (voted_users.c.voted_id == id),
        secondaryjoin = (voted_users.c.answer_id == id),
        backref = db.backref('voted_users', lazy = 'dynamic'),
        lazy = 'dynamic')

    def is_voted_user(self):
        return self.voted.filter(voted_users.c.voted_id == self.id).count() > 0

    def like(self):
        if not self.is_voted_user():
            self.voted.append(self)
            self.rating += 1
            return False
        return True

    def __repr__(self):
        return '<Answer %r>' % (self.body)
