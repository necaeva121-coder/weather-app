from datetime import datetime

from ..extensions import db


class WeatherQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    city = db.Column(db.String(120), nullable=False)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    wind_speed = db.Column(db.Float)
    description = db.Column(db.String(120))
    icon = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('weather_queries', lazy='dynamic'))


class FavoriteCity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('favorite_cities', lazy='dynamic'))

