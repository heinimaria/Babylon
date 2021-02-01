from Babylon import db, login_manager
from datetime import datetime
from flask_login import UserMixin



# this is essential for the app to manage your sessions
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default_user.png')
    password = db.Column(db.String(60), nullable=False)

    houses = db.relationship('House', backref='user', lazy='dynamic')

    def __repr__(self):
        return f"User('{self.name}', '{self.email}')"


class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(35), nullable=False)
    location = db.Column(db.String(35), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default_plant.png')
    date_watered = db.Column(db.DateTime)
    watering_frequency = db.Column(db.Integer, nullable=False)
    watering_history = db.Column(db.DateTime)
    next_watering = db.Column(db.DateTime)

    house_id = db.Column(db.Integer, db.ForeignKey('house.id'), nullable=False)

    def __repr__(self):
        return f"Plant('{self.name}', '{self.location}')"


class House(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(35), nullable=False)
    address_first_line = db.Column(db.String(35))
    address_second_line = db.Column(db.String(35))
    postcode = db.Column(db.String(10))
    town = db.Column(db.String(25))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    plants = db.relationship('Plant', backref='house', lazy='dynamic')

    def __repr__(self):
        return f"House('{self.name}')"
