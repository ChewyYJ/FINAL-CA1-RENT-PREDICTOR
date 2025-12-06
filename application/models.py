from application import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# USER MODEL
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    # Relationship to predictions
    predictions = db.relationship("Prediction", backref="user", lazy=True)

    # Password helpers
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# PREDICTION MODEL
class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    area = db.Column(db.Float)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    furnishing = db.Column(db.String(15))
    age_of_listing = db.Column(db.Integer)
    property_type = db.Column(db.String(20))
    city = db.Column(db.String(50))
    location = db.Column(db.String(100))

    predicted_rent = db.Column(db.Float)

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # for user authentication - link prediction → user
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    def __repr__(self):
        return f'<Prediction {self.id}: {self.predicted_rent}>'
