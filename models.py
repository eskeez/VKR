from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime



db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    subscription = db.relationship('Subscription', backref='user', uselist=False)

    def is_active(self):
        return self.is_active


class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    active = db.Column(db.Boolean, default=False)


class Film(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    poster = db.Column(db.String(200), nullable=False)
    video = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    director = db.Column(db.String(100), nullable=False)
    actors = db.Column(db.String(100), nullable=False)
    view = db.Column(db.Integer, default=0)  # Add views field

    def __repr__(self):
        return '<Film %r>' % self.id

    reviews = db.relationship('Review', backref='film', lazy=True)
    view_relationship = db.relationship('View', backref='film_view_relationship',
                                        lazy=True)  # Rename relationship to view_relationship


class View(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('views', lazy=True))
    film = db.relationship('Film',
                           backref=db.backref('views_relationship', lazy=True))


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'))
    rating = db.Column(db.Integer)

    film = db.relationship('Film', backref=db.backref('film_views', lazy=True))


# Модель для избранных фильмов
class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'), nullable=False)
    film = db.relationship('Film', backref=db.backref('favorites', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('favorites', lazy=True))


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'), nullable=False)
    user = db.relationship('User', backref='reviews')

    def __repr__(self):
        return f"Review('{self.comment}', '{self.date_posted}')"


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    film_link = db.Column(db.String(255), nullable=True)
    director = db.Column(db.String(255), nullable=True)
    actors = db.Column(db.Text, nullable=True)
    year = db.Column(db.String(4), nullable=True)
    genre = db.Column(db.String(255), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    poster_link = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(), nullable=True)



