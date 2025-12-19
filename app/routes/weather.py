from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import CityForm
from ..functions import fetch_weather
from ..models.weather import FavoriteCity, WeatherQuery
from ..config import Config

weather = Blueprint('weather', __name__)


@weather.route('/', methods=['GET', 'POST'])
def landing():
    form = CityForm()
    city_from_query = request.args.get('city')
    if form.validate_on_submit():
        city_from_query = form.city.data
        return redirect(url_for('weather.dashboard', city=city_from_query))

    display_city = city_from_query or Config.DEFAULT_CITY
    return render_template('weather/landing.html', form=form, display_city=display_city)


@weather.route('/weather', methods=['GET', 'POST'])
def dashboard():
    form = CityForm()
    weather_data = None
    favorites = []

    city_from_query = request.args.get('city')
    if form.validate_on_submit():
        city_from_query = form.city.data

    city_to_fetch = city_from_query or Config.DEFAULT_CITY

    if city_to_fetch:
        try:
            weather_data = fetch_weather(city_to_fetch)
            if current_user.is_authenticated:
                db.session.add(
                    WeatherQuery(
                        user_id=current_user.id,
                        city=weather_data["city"],
                        temperature=weather_data["current"]["temperature"],
                        humidity=weather_data["current"]["humidity"],
                        wind_speed=weather_data["current"]["wind_speed"],
                        description=weather_data["current"]["description"],
                        icon=weather_data["current"]["icon"],
                    )
                )
                db.session.commit()
        except Exception as exc:  # pragma: no cover - defensive UX
            flash(f"Не удалось получить погоду: {exc}", "danger")

    if current_user.is_authenticated:
        favorites = (
            FavoriteCity.query.filter_by(user_id=current_user.id)
            .order_by(FavoriteCity.created_at.desc())
            .all()
        )

    return render_template('weather/dashboard.html', form=form, weather=weather_data, favorites=favorites)


@weather.post('/favorites/add')
@login_required
def add_favorite():
    city = request.form.get('city')
    if not city:
        flash("Город не задан", "warning")
        return redirect(url_for('weather.dashboard'))

    exists = FavoriteCity.query.filter_by(user_id=current_user.id, city=city).first()
    if exists:
        flash("Город уже в избранном", "info")
    else:
        db.session.add(FavoriteCity(user_id=current_user.id, city=city))
        db.session.commit()
        flash("Город добавлен в избранное", "success")

    return redirect(url_for('weather.dashboard', city=city))


@weather.post('/favorites/<int:fav_id>/remove')
@login_required
def remove_favorite(fav_id: int):
    favorite = FavoriteCity.query.filter_by(id=fav_id, user_id=current_user.id).first()
    if not favorite:
        flash("Избранный город не найден", "warning")
    else:
        db.session.delete(favorite)
        db.session.commit()
        flash("Город удалён из избранного", "success")
    return redirect(url_for('weather.dashboard'))


@weather.route('/history')
@login_required
def history():
    queries = (
        WeatherQuery.query.filter_by(user_id=current_user.id)
        .order_by(WeatherQuery.created_at.desc())
        .limit(50)
        .all()
    )
    return render_template('weather/history.html', queries=queries)


@weather.route('/about')
def about():
    return render_template('weather/about.html')

