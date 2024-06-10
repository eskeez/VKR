import pytest
from app import app, db, User, Subscription, Film, View, Rating, Favorite, Review, Submission
import sqlalchemy

class TestConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    WTF_CSRF_ENABLED = False

@pytest.fixture
def test_app():
    test_app = app
    test_app.config.from_object(TestConfig)
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()

def test_user_creation(test_app):
    with test_app.app_context():
        user = User(username="test_user", email="test@example.com", password="testpassword")
        db.session.add(user)
        db.session.commit()
        assert User.query.filter_by(username="test_user").first() is not None

def test_subscription_creation(test_app):
    with test_app.app_context():
        user = User(username="test_user", email="test@example.com", password="testpassword")
        subscription = Subscription(user=user)
        db.session.add(user)
        db.session.add(subscription)
        db.session.commit()
        assert Subscription.query.filter_by(user_id=user.id).first() is not None

def test_film_creation(test_app):
    with test_app.app_context():
        film = Film(title="Test Film", genre="Action", description="Test description", poster="poster.jpg",
                    video="video.mp4", rating=5, year=2022, director="Test Director", actors="Test Actor 1, Test Actor 2")
        db.session.add(film)
        db.session.commit()
        assert Film.query.filter_by(title="Test Film").first() is not None

def test_view_creation(test_app):
    with test_app.app_context():
        user = User(username="test_user", email="test@example.com", password="testpassword")
        film = Film(title="Test Film", genre="Action", description="Test description", poster="poster.jpg",
                    video="video.mp4", rating=5, year=2022, director="Test Director", actors="Test Actor 1, Test Actor 2")
        view = View(user=user, film=film)
        db.session.add(user)
        db.session.add(film)
        db.session.add(view)
        db.session.commit()
        assert View.query.filter_by(user_id=user.id, film_id=film.id).first() is not None

def test_rating_creation(test_app):
    with test_app.app_context():
        # Создаем пользователя
        user = User(username="test_user", email="test@example.com", password="testpassword")
        db.session.add(user)
        db.session.commit()

        # Создаем фильм
        film = Film(title="Test Film", genre="Action", description="Test description", poster="poster.jpg",
                    video="video.mp4", rating=5, year=2022, director="Test Director", actors="Test Actor 1, Test Actor 2")
        db.session.add(film)
        db.session.commit()

        # Создаем рейтинг
        rating = Rating(user_id=user.id, film_id=film.id, rating=4)
        db.session.add(rating)
        db.session.commit()

        assert Rating.query.filter_by(user_id=user.id, film_id=film.id, rating=4).first() is not None

def test_favorite_creation(test_app):
    with test_app.app_context():
        user = User(username="test_user", email="test@example.com", password="testpassword")
        film = Film(title="Test Film", genre="Action", description="Test description", poster="poster.jpg",
                    video="video.mp4", rating=5, year=2022, director="Test Director", actors="Test Actor 1, Test Actor 2")
        favorite = Favorite(user=user, film=film)
        db.session.add(user)
        db.session.add(film)
        db.session.add(favorite)
        db.session.commit()
        assert Favorite.query.filter_by(user_id=user.id, film_id=film.id).first() is not None

def test_review_creation(test_app):
    with test_app.app_context():
        user = User(username="test_user", email="test@example.com", password="testpassword")
        film = Film(title="Test Film", genre="Action", description="Test description", poster="poster.jpg",
                    video="video.mp4", rating=5, year=2022, director="Test Director", actors="Test Actor 1, Test Actor 2")
        review = Review(comment="Test comment", user=user, film=film)
        db.session.add(user)
        db.session.add(film)
        db.session.add(review)
        db.session.commit()
        assert Review.query.filter_by(user_id=user.id, film_id=film.id).first() is not None

def test_submission_creation(test_app):
    with test_app.app_context():
        submission = Submission(title="Test Submission", film_link="film_link", director="Test Director",
                                actors="Test Actor 1, Test Actor 2", year="2022", genre="Action",
                                summary="Test summary", poster_link="poster_link", status="Pending")
        db.session.add(submission)
        db.session.commit()
        assert Submission.query.filter_by(title="Test Submission").first() is not None