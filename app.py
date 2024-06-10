from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
import cloudinary
from cloudinary.uploader import upload
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, asc
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import login_user, login_required, logout_user, LoginManager, current_user
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from flask_login import UserMixin

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired
from datetime import datetime

app = Flask(__name__)
bootstrap = Bootstrap(app)
login_manager = LoginManager(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.secret_key = 'cats'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Путь для временного хранения загруженных файлов
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Установка конфигурации Flask
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


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
                           backref=db.backref('views_relationship', lazy=True))  # Изменить backref на что-то другое


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    film_id = db.Column(db.Integer, db.ForeignKey('film.id'))
    rating = db.Column(db.Integer)

    film = db.relationship('Film', backref=db.backref('film_views', lazy=True))  # Rename backref to film_views


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


with app.app_context():
    db.create_all()

# Конфигурация Cloudinary
cloudinary.config(
    cloud_name='dtsewo1eq',
    api_key='185364932432476',
    api_secret='0KFpWNaLxWxniRaW_1yS2e81yn0'
)


# Создание административного интерфейса
admin = Admin(app, name='NativeCinema', template_mode='bootstrap3')

# Добавление модели Film в административный интерфейс
admin.add_view(ModelView(Film, db.session, name='Фильмы'))
admin.add_view(ModelView(User, db.session, name='Пользователи'))
admin.add_view(ModelView(Review, db.session, name='Рецензии'))
admin.add_view(ModelView(Subscription, db.session, name='Подписки'))
admin.add_view(ModelView(Submission, db.session, name='Заявки'))


@app.route('/')
def home():  # put application's code here
    films = Film.query.all()

    return render_template('home.html', films=films)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form['search_query']
        # Выполнить поиск фильмов по введенному названию
        films = Film.query.filter(Film.title.like(f'%{search_query}%')).all()
        # Обработайте результаты поиска
        return render_template('search_result.html', films=films)
    else:
        return render_template('home.html')


class ReviewForm(FlaskForm):
    comment = TextAreaField(' ', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/movie/<int:film_id>', methods=['GET', 'POST'])
def movie(film_id):
    film = Film.query.get_or_404(film_id)
    form = ReviewForm()
    film.view += 1
    db.session.commit()
    if current_user.is_authenticated:
        view = View(user_id=current_user.id, film_id=film.id)
        db.session.add(view)
        db.session.commit()
    if request.method == 'POST':
        if form.validate_on_submit():
            # Обработка отправки формы рецензии
            comment = form.comment.data
            user_id = current_user.id

            new_review = Review(comment=comment, user_id=user_id, film_id=film_id)
            db.session.add(new_review)
            db.session.commit()

        try:
            # Обработка отправки рейтинга
            rating_value = int(request.form['rating'])
            user_id = current_user.id

            existing_rating = Rating.query.filter_by(user_id=user_id, film_id=film_id).first()
            if existing_rating:
                existing_rating.rating = rating_value
            else:
                new_rating = Rating(user_id=user_id, film_id=film_id, rating=rating_value)
                db.session.add(new_rating)
            db.session.commit()
            calculate_average_rating(film_id)
        except KeyError:
            # Обработка случая, когда пользователь не указал рейтинг
            pass

        return redirect(url_for('movie', film_id=film.id))

    return render_template('movie.html', film=film, form=form)


@app.route('/analytics')
@login_required
def analytics():
    total_users = User.query.count()
    active_subscriptions = Subscription.query.filter_by(active=True).count()
    inactive_subscriptions = Subscription.query.filter_by(active=False).count()
    total_films = Film.query.count()
    most_viewed_films = Film.query.order_by(Film.view.desc()).limit(10).all()
    most_active_users = db.session.query(User.username, db.func.count(View.id).label('total_views')) \
        .join(View).group_by(User.username) \
        .order_by(db.func.count(View.id).desc()).limit(10).all()

    film_titles = [film.title for film in most_viewed_films]
    film_views = [film.view for film in most_viewed_films]

    user_names = [user.username for user in most_active_users]
    user_views = [user.total_views for user in most_active_users]

    return render_template('analytics.html', total_users=total_users,
                           active_subscriptions=active_subscriptions,
                           inactive_subscriptions=inactive_subscriptions,
                           total_films=total_films,
                           film_titles=film_titles,
                           film_views=film_views,
                           user_names=user_names,
                           user_views=user_views)


def calculate_average_rating(film_id):
    film = Film.query.get(film_id)
    ratings = Rating.query.filter_by(film_id=film_id).all()

    total_rating = sum(r.rating for r in ratings)
    average_rating = total_rating / len(ratings) if ratings else 0

    film.rating = int(round(average_rating))
    db.session.commit()


@app.route('/catalog', methods=['GET', 'POST'])
def catalog():
    query = Film.query

    if request.method == 'POST':
        # Обработка отправленной формы фильтров
        genres = request.form.getlist('genre')
        year = request.form['year']
        director = request.form['director']
        rating = request.form['rating']

        # Настройка фильтров на основе данных из формы
        if genres:
            query = query.filter(Film.genre.in_(genres))
        if year:
            query = query.filter(Film.year == year)
        if director:
            query = query.filter(Film.director.ilike(f"%{director}%"))
        if rating:
            query = query.filter(Film.rating == rating)

    # Обработка сортировки из GET-запроса
    sort_by = request.args.get('sort_by')
    if sort_by == 'rating_desc':
        query = query.order_by(desc(Film.rating))
    elif sort_by == 'rating_asc':
        query = query.order_by(asc(Film.rating))
    elif sort_by == 'year_desc':
        query = query.order_by(desc(Film.year))
    elif sort_by == 'year_asc':
        query = query.order_by(asc(Film.year))

    films = query.all()
    return render_template('catalog.html', films=films)


@login_manager.user_loader
def loader_user(user_id):
    return User.query.get(user_id)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return 'Username and password fields are required'

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))

        return 'Invalid username or password'

    return render_template("login.html")


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = User.query.first()  # Получите пользователя из базы данных, например

    # Обработка изменений профиля
    new_password = request.form.get('new_password')
    new_username = request.form.get('new_username')

    if new_password:
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        current_user.password = hashed_password
    if new_username:
        current_user.username = new_username

    db.session.commit()

    # Проверяем статус подписки текущего пользователя
    subscription_active = current_user.subscription.active if current_user.subscription else False
    print("подписка ", current_user.subscription.active)

    flash('Изменения сохранены.', 'success')
    return render_template('profile.html', user=current_user, subscription_active=subscription_active)


@app.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    if not current_user.subscription:
        subscription = Subscription(user_id=current_user.id, active=True)
        db.session.add(subscription)
    else:
        current_user.subscription.active = True
    db.session.commit()
    flash('Подписка успешно активирована!', 'success')
    return redirect(url_for('profile'))


@app.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    if current_user.subscription:
        current_user.subscription.active = False
        db.session.commit()
        flash('Подписка успешно отменена!', 'success')
    return redirect(url_for('profile'))


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if request.method == "POST":
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            return jsonify({'message': 'Please provide all required fields.'}), 400

        # Проверяем, существует ли пользователь с таким именем или email'ом
        existing_user = User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'message': 'Username or email already exists. Please choose another one.'}), 400

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        new_subscription = Subscription(user_id=new_user.id, active=False)  # или True, в зависимости от вашей логики
        db.session.add(new_subscription)
        db.session.commit()

        flash('Регистрация успешна', 'success')
        return redirect(url_for('login'))
    return render_template("registration.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/admin1', methods=['GET', 'POST'])
@login_required
def admin1():
    if current_user.username != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        submission_id = request.form.get('submission_id')
        submission = Submission.query.get(submission_id)
        if 'accept' in request.form and submission:
            submission.status = 'Accepted'
            db.session.commit()
            flash('Submission accepted successfully.', 'success')
        elif 'reject' in request.form and submission:
            submission.status = 'Rejected'
            db.session.commit()
            flash('Submission rejected successfully.', 'success')

        elif submission:
            # Загрузка информации о фильме
            title = request.form.get('title')
            genre = request.form.get('genre')
            description = request.form.get('description')
            year = request.form.get('year')
            director = request.form.get('director')
            actors = request.form.get('actors')

            # Сохранение изображения на сервере
            poster_file = request.files['poster']
            poster_filename = secure_filename(poster_file.filename)
            poster_path = os.path.join(app.config['UPLOAD_FOLDER'], poster_filename)
            poster_file.save(poster_path)

            # Загрузка изображения на Cloudinary
            response = cloudinary.uploader.upload(poster_path)
            poster_url = response['url']

            # Сохранение видео на сервере
            video_file = request.files['video']
            video_filename = secure_filename(video_file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)
            video_file.save(video_path)

            # Загрузка видео на Cloudinary
            video_response = cloudinary.uploader.upload(video_path, resource_type="video")
            video_url = video_response['url']

            # Создание нового объекта фильма
            new_film = Film(title=title, genre=genre, description=description, poster=poster_url, video=video_url,
                            year=year, director=director, actors=actors)
            db.session.add(new_film)
            db.session.commit()

            # Удаление временного изображения с сервера
            os.remove(poster_path)
            os.remove(video_path)

        return redirect(url_for('admin1'))

    submissions = Submission.query.all()
    selected_submission_id = request.args.get('submission_id')
    selected_submission = Submission.query.get(selected_submission_id) if selected_submission_id else None

    return render_template('admin.html', submissions=submissions, selected_submission=selected_submission)


favorites = []


@app.route('/add_to_favorites', methods=['POST'])
@login_required
def add_to_favorites():
    film_id = int(request.form['film_id'])
    film = Film.query.get(film_id)
    if film:
        # Проверяем, есть ли фильм уже в избранном для текущего пользователя
        existing_favorite = Favorite.query.filter_by(film_id=film_id, user_id=current_user.id).first()
        if not existing_favorite:
            favorite = Favorite(user_id=current_user.id, film_id=film.id)
            db.session.add(favorite)
            db.session.commit()
            return redirect(url_for('favorites'))
        else:
            return "Фильм уже добавлен в избранное", 400
    return "Фильм не найден", 404


@app.route('/remove_from_favorites', methods=['POST'])
@login_required
def remove_from_favorites():
    film_id = int(request.form['film_id'])
    favorite = Favorite.query.filter_by(film_id=film_id, user_id=current_user.id).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return redirect(url_for('favorites'))
    return "Фильм не найден в избранном", 404


@app.route('/favorites')
@login_required
def favorites():
    # Извлекаем избранные фильмы для текущего пользователя
    favorite_films = Favorite.query.filter_by(user_id=current_user.id).all()
    return render_template('favorites.html', favorite_films=favorite_films)


@app.route('/place_movie', methods=['GET', 'POST'])
def place_movie():
    if request.method == 'POST':
        title = request.form.get('title')
        film_link = request.form.get('film_link')
        director = request.form.get('director')
        actors = request.form.get('actors')
        year = request.form.get('year')
        genre = request.form.get('genre')
        summary = request.form.get('summary')
        poster_link = request.form.get('poster_link')
        status = "new"
        submission = Submission(title=title, film_link=film_link, director=director,
                                actors=actors, year=year, genre=genre, summary=summary,
                                poster_link=poster_link,status=status)
        db.session.add(submission)
        db.session.commit()

        return redirect(url_for('place_movie'))

    return render_template('place_movie.html')


# Страница с рекомендациями
@app.route('/recommendations')
@login_required
def recommendations():
    user_id = current_user.id
    recommendations1 = get_recommendations(user_id)
    return render_template('recommendations.html', recommendations=recommendations1)


def get_recommendations(user_id):
    # Проверка соединения с базой данных
    if not db.session.is_active:
        raise Exception("Database connection is not established.")

    # Запрос рейтингов и фильмов из базы данных
    ratings = db.session.query(Rating).all()
    films = db.session.query(Film).all()

    # Проверка на пустоту данных
    if not ratings or not films:
        return []

    # Преобразование данных в DataFrame
    ratings_df = pd.DataFrame([(r.user_id, r.film_id, r.rating) for r in ratings],
                              columns=['user_id', 'film_id', 'rating'])
    films_df = pd.DataFrame([(f.id, f.title) for f in films], columns=['film_id', 'title'])

    # Построение матрицы пользователь-фильм
    user_film_matrix = ratings_df.pivot_table(index='user_id', columns='film_id', values='rating').fillna(0)

    # Вычисление косинусного сходства между пользователями
    user_similarity = cosine_similarity(user_film_matrix)
    user_similarity_df = pd.DataFrame(user_similarity, index=user_film_matrix.index, columns=user_film_matrix.index)

    # Получение пользователей, похожих на текущего пользователя
    similar_users = user_similarity_df[user_id].sort_values(ascending=False).index[1:]

    # Получение фильмов, которые понравились похожим пользователям
    film_recommendations = pd.Series(dtype='float64')
    for user in similar_users:
        liked_films = user_film_matrix.loc[user]
        liked_films = liked_films[liked_films > 3]  # Фильмы с рейтингом > 3
        film_recommendations = pd.concat([film_recommendations, liked_films])

    # Удаление фильмов, которые пользователь уже смотрел
    watched_films = user_film_matrix.loc[user_id]
    watched_films = watched_films[watched_films > 0].index
    film_recommendations = film_recommendations[~film_recommendations.index.isin(watched_films)]

    # Подсчет наиболее рекомендуемых фильмов
    film_recommendations = film_recommendations.groupby(film_recommendations.index).mean()
    recommended_film_ids = film_recommendations.sort_values(ascending=False).index[:5]

    # Получение информации о рекомендуемых фильмах
    recommended_films = db.session.query(Film).filter(Film.id.in_(recommended_film_ids)).all()
    return recommended_films
